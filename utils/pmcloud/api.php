<?php
// api.php

// 1. CONFIGURAÇÕES E SEGURANÇA
define('API_TOKEN', 'sua_chave_secreta_aqui_123'); // MUDE ISSO!
define('DIR_COFRE', __DIR__ . '/cofre/');
define('DIR_TEMP', __DIR__ . '/temp/');
define('ARQUIVO_BD', __DIR__ . '/banco.sqlite');

header('Content-Type: application/json');

// Verifica o Token
$token_recebido = $_SERVER['HTTP_X_VC_API_TOKEN'] ?? '';
if ($token_recebido !== API_TOKEN) {
    http_response_code(401);
    die(json_encode(["erro" => "Não autorizado."]));
}

// 2. CONEXÃO E PREPARAÇÃO DO BANCO (SQLite)
$pdo = new PDO('sqlite:' . ARQUIVO_BD);
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

// Cria as tabelas se não existirem
$pdo->exec("
    CREATE TABLE IF NOT EXISTS backups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
        pasta_alvo TEXT
    );
    CREATE TABLE IF NOT EXISTS arquivos_fisicos (
        hash_arquivo TEXT PRIMARY KEY, 
        tamanho INTEGER
    );
    CREATE TABLE IF NOT EXISTS backup_itens (
        backup_id INTEGER,
        hash_arquivo TEXT,
        caminho_relativo TEXT,
        PRIMARY KEY (backup_id, caminho_relativo)
    );
");

// 3. ROTEAMENTO DAS AÇÕES
$acao = $_POST['acao'] ?? '';
if (!$acao && isset($_SERVER['CONTENT_TYPE']) && strpos($_SERVER['CONTENT_TYPE'], 'application/json') !== false) {
    $inputJSON = file_get_contents('php://input');
    $input = json_decode($inputJSON, TRUE);
    $acao = $input['acao'] ?? '';
}

switch ($acao) {
    // ---------------------------------------------------------
    // FLUXO DE BACKUP: ETAPA 1 (Verificar o que falta)
    // ---------------------------------------------------------
    case 'verificar_arquivos':
        $arquivos_locais = $input['arquivos'] ?? [];
        $arquivos_para_upload = [];

        $stmt = $pdo->prepare("SELECT hash_arquivo FROM arquivos_fisicos WHERE hash_arquivo = ?");

        foreach ($arquivos_locais as $arq) {
            $stmt->execute([$arq['hash']]);
            if (!$stmt->fetch()) {
                // Se não achou o hash no cofre, precisa fazer upload
                $arquivos_para_upload[] = $arq['caminho_relativo'];
            }
        }

        echo json_encode([
            "status" => "sucesso",
            "arquivos_para_upload" => $arquivos_para_upload
        ]);
        break;

    // ---------------------------------------------------------
    // FLUXO DE BACKUP: ETAPA 2 (Receber ZIP e gravar no banco)
    // ---------------------------------------------------------
    case 'upload_backup':
        $pasta_alvo = $_POST['pasta_alvo'] ?? 'padrao';
        $metadados = json_decode($_POST['metadados'], true); // Hashes enviados pelo Python
        
        // Cria o registro da Fotografia
        $stmt = $pdo->prepare("INSERT INTO backups (pasta_alvo) VALUES (?)");
        $stmt->execute([$pasta_alvo]);
        $backup_id = $pdo->lastInsertId();

        // Se veio arquivo ZIP com os novos arquivos, extrai para o cofre
        if (isset($_FILES['arquivo_zip']) && $_FILES['arquivo_zip']['error'] === UPLOAD_ERR_OK) {
            $zip_temp = $_FILES['arquivo_zip']['tmp_name'];
            $zip = new ZipArchive;
            if ($zip->open($zip_temp) === TRUE) {
                // Extrai temporariamente para ler o conteúdo
                $dir_extracao = DIR_TEMP . uniqid('ext_');
                mkdir($dir_extracao);
                $zip->extractTo($dir_extracao);
                $zip->close();

                // Move os arquivos para o cofre usando o HASH como nome
                foreach ($metadados as $arq) {
                    $caminho_extraido = $dir_extracao . '/' . $arq['caminho_relativo'];
                    if (file_exists($caminho_extraido)) {
                        $destino_cofre = DIR_COFRE . $arq['hash'];
                        rename($caminho_extraido, $destino_cofre);
                        
                        // Registra o arquivo físico novo
                        $stmt_fisico = $pdo->prepare("INSERT OR IGNORE INTO arquivos_fisicos (hash_arquivo, tamanho) VALUES (?, ?)");
                        $stmt_fisico->execute([$arq['hash'], $arq['tamanho']]);
                    }
                }
                // Limpa a pasta de extração temporária
                array_map('unlink', glob("$dir_extracao/*.*"));
                rmdir($dir_extracao);
            }
        }

        // Liga a fotografia (backup_id) a TODOS os arquivos (novos e velhos)
        $stmt_item = $pdo->prepare("INSERT INTO backup_itens (backup_id, hash_arquivo, caminho_relativo) VALUES (?, ?, ?)");
        foreach ($metadados as $arq) {
            $stmt_item->execute([$backup_id, $arq['hash'], $arq['caminho_relativo']]);
        }

        echo json_encode(["status" => "sucesso", "mensagem" => "Backup $backup_id concluído."]);
        break;

    // ---------------------------------------------------------
    // FLUXO DE RESTAURAÇÃO (PULL)
    // ---------------------------------------------------------
    case 'solicitar_pull':
        $pasta_alvo = $input['pasta_alvo'];
        $data_alvo = $input['data_alvo'] ?? null;

        // Acha o backup mais recente ou o mais próximo da data
        if ($data_alvo) {
            $stmt = $pdo->prepare("SELECT id FROM backups WHERE pasta_alvo = ? AND data_criacao <= ? ORDER BY data_criacao DESC LIMIT 1");
            $stmt->execute([$pasta_alvo, $data_alvo . ' 23:59:59']);
        } else {
            $stmt = $pdo->prepare("SELECT id FROM backups WHERE pasta_alvo = ? ORDER BY data_criacao DESC LIMIT 1");
            $stmt->execute([$pasta_alvo]);
        }
        
        $backup = $stmt->fetch();
        if (!$backup) {
            die(json_encode(["erro" => "Nenhum backup encontrado para esta pasta/data."]));
        }

        // Pega os itens dessa fotografia
        $stmt_itens = $pdo->prepare("SELECT hash_arquivo, caminho_relativo FROM backup_itens WHERE backup_id = ?");
        $stmt_itens->execute([$backup['id']]);
        $arquivos = $stmt_itens->fetchAll(PDO::FETCH_ASSOC);

        // Monta o ZIP temporário
        $nome_zip = "pull_{$pasta_alvo}_" . time() . ".zip";
        $caminho_zip = DIR_TEMP . $nome_zip;
        
        $zip = new ZipArchive;
        if ($zip->open($caminho_zip, ZipArchive::CREATE) === TRUE) {
            foreach ($arquivos as $arq) {
                $caminho_no_cofre = DIR_COFRE . $arq['hash_arquivo'];
                if (file_exists($caminho_no_cofre)) {
                    $zip->addFile($caminho_no_cofre, $arq['caminho_relativo']);
                }
            }
            $zip->close();
        }

        // Retorna a URL (ajuste 'seudominio.com.br' para a URL real da sua API)
        $protocolo = isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] === 'on' ? "https" : "http";
        $url_base = $protocolo . "://" . $_SERVER['HTTP_HOST'] . dirname($_SERVER['REQUEST_URI']);
        
        echo json_encode([
            "status" => "sucesso",
            "download_url" => $url_base . "/temp/" . $nome_zip,
            "total_arquivos" => count($arquivos)
        ]);
        break;

    // ---------------------------------------------------------
    // FLUXO DE LISTAGEM (-ls)
    // ---------------------------------------------------------
    case 'listar':
        $pasta_alvo = $input['pasta_alvo'] ?? null;
        
        if ($pasta_alvo && $pasta_alvo !== 'ALL') {
            // Histórico de uma pasta específica
            $stmt = $pdo->prepare("
                SELECT b.data_criacao, COUNT(bi.hash_arquivo) as qtd_arquivos 
                FROM backups b 
                LEFT JOIN backup_itens bi ON b.id = bi.backup_id 
                WHERE b.pasta_alvo = ? 
                GROUP BY b.id 
                ORDER BY b.data_criacao DESC
            ");
            $stmt->execute([$pasta_alvo]);
            $historico = $stmt->fetchAll(PDO::FETCH_ASSOC);
            
            echo json_encode(["status" => "sucesso", "tipo" => "historico", "dados" => $historico]);
        } else {
            // Resumo geral das pastas
            $stmt = $pdo->query("
                SELECT pasta_alvo, COUNT(id) as total_backups, MAX(data_criacao) as ultimo_backup 
                FROM backups 
                GROUP BY pasta_alvo 
                ORDER BY pasta_alvo
            ");
            $pastas = $stmt->fetchAll(PDO::FETCH_ASSOC);
            
            // Calcula o tamanho total ocupado fisicamente no cofre
            $stmt_tam = $pdo->query("SELECT SUM(tamanho) as tamanho_total FROM arquivos_fisicos");
            $tamanho_total = $stmt_tam->fetch(PDO::FETCH_ASSOC)['tamanho_total'];

            echo json_encode(["status" => "sucesso", "tipo" => "resumo", "dados" => $pastas, "tamanho_total" => $tamanho_total]);
        }
        break;

    // ---------------------------------------------------------
    // FLUXO DE EXCLUSÃO COM GARBAGE COLLECTION (-rm)
    // ---------------------------------------------------------
    case 'deletar':
        $pasta_alvo = $input['pasta_alvo'] ?? null;
        if (!$pasta_alvo) {
            die(json_encode(["erro" => "Pasta não informada."]));
        }

        // 1. Encontra todos os backups dessa pasta
        $stmt_backups = $pdo->prepare("SELECT id FROM backups WHERE pasta_alvo = ?");
        $stmt_backups->execute([$pasta_alvo]);
        $backups = $stmt_backups->fetchAll(PDO::FETCH_COLUMN);

        if (empty($backups)) {
            die(json_encode(["erro" => "Pasta não encontrada na nuvem."]));
        }

        $pdo->beginTransaction();
        try {
            // 2. Remove os vínculos em backup_itens e os registros em backups
            $in_placeholders = str_repeat('?,', count($backups) - 1) . '?';
            $stmt_del_itens = $pdo->prepare("DELETE FROM backup_itens WHERE backup_id IN ($in_placeholders)");
            $stmt_del_itens->execute($backups);

            $stmt_del_backups = $pdo->prepare("DELETE FROM backups WHERE pasta_alvo = ?");
            $stmt_del_backups->execute([$pasta_alvo]);

            // 3. O Pulo do Gato (Garbage Collection): Encontra os "órfãos"
            // Hashes na tabela 'arquivos_fisicos' que não existem mais em 'backup_itens'
            $stmt_orfaos = $pdo->query("
                SELECT f.hash_arquivo 
                FROM arquivos_fisicos f 
                LEFT JOIN backup_itens bi ON f.hash_arquivo = bi.hash_arquivo 
                WHERE bi.hash_arquivo IS NULL
            ");
            $orfaos = $stmt_orfaos->fetchAll(PDO::FETCH_COLUMN);

            $tamanho_liberado = 0;
            $arquivos_apagados = 0;

            // 4. Apaga fisicamente os órfãos do HD e do Banco
            $stmt_del_fisico = $pdo->prepare("DELETE FROM arquivos_fisicos WHERE hash_arquivo = ?");
            foreach ($orfaos as $hash) {
                $caminho = DIR_COFRE . $hash;
                if (file_exists($caminho)) {
                    $tamanho_liberado += filesize($caminho);
                    unlink($caminho); // Apaga o arquivo do servidor
                }
                $stmt_del_fisico->execute([$hash]);
                $arquivos_apagados++;
            }

            $pdo->commit();

            echo json_encode([
                "status" => "sucesso",
                "mensagem" => "Histórico da pasta '$pasta_alvo' excluído com segurança.",
                "orfaos_removidos" => $arquivos_apagados,
                "espaco_liberado" => $tamanho_liberado
            ]);

        } catch (Exception $e) {
            $pdo->rollBack();
            die(json_encode(["erro" => "Erro ao deletar: " . $e->getMessage()]));
        }
        break;

    default:
        http_response_code(400);
        echo json_encode(["erro" => "Ação não reconhecida."]);
        break;
}