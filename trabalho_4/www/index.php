<?php
$apiEndpoint = getenv("API_ENDPOINT") ?: "http://api-python:5000/api/";
$url = $_GET["url"] ?? "";
$result = null;
$error = null;

if ($url) {
    $requestUrl = $apiEndpoint . "?url=" . urlencode($url);

    $response = @file_get_contents($requestUrl);

    if ($response === false) {
        $error = "Erro ao chamar a API.";
    } else {
        $result = json_decode($response, true);
    }
}
?>

<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Link Extractor</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 32px;
            background: #f5f5f5;
        }

        main {
            max-width: 900px;
            margin: auto;
            background: #fff;
            padding: 24px;
            border-radius: 8px;
        }

        input {
            width: 75%;
            padding: 10px;
        }

        button {
            padding: 10px 16px;
            cursor: pointer;
        }

        .error {
            color: #b00020;
            margin-top: 16px;
        }

        ul {
            line-height: 1.7;
        }

        code {
            background: #eee;
            padding: 2px 4px;
        }
    </style>
</head>
<body>
<main>
    <h1>Link Extractor</h1>

    <form method="GET">
        <input
            type="url"
            name="url"
            placeholder="https://example.com"
            value="<?= htmlspecialchars($url) ?>"
            required
        >
        <button type="submit">Extract Links</button>
    </form>

    <?php if ($error): ?>
        <p class="error"><?= htmlspecialchars($error) ?></p>
    <?php endif; ?>

    <?php if ($result): ?>
        <h2>Resultado</h2>

        <p><strong>URL:</strong> <?= htmlspecialchars($result["url"] ?? "") ?></p>
        <p><strong>Total de links:</strong> <?= count($result["links"] ?? []) ?></p>
        <p><strong>Cache:</strong> <?= !empty($result["cached"]) ? "Sim" : "Não" ?></p>
        <p><strong>Serviço:</strong> <?= htmlspecialchars($result["service"] ?? "") ?></p>

        <h3>Links encontrados</h3>

        <ul>
            <?php foreach (($result["links"] ?? []) as $link): ?>
                <li>
                    <a href="<?= htmlspecialchars($link) ?>" target="_blank">
                        <?= htmlspecialchars($link) ?>
                    </a>
                </li>
            <?php endforeach; ?>
        </ul>
    <?php endif; ?>
</main>
</body>
</html>