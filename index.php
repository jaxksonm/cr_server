<?php
session_start();

// Database credentials
$host = 'localhost'; // Use IP to avoid socket issues
$db   = 'clash_login';
$user = 'root';
$pass = 'YourRootPasswordHere';
$charset = 'utf8mb4';

// PDO setup
$dsn = "mysql:host=$host;dbname=$db;charset=$charset";
$options = [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
];

try {
    $pdo = new PDO($dsn, $user, $pass, $options);
} catch (\PDOException $e) {
    die("Database connection failed: " . $e->getMessage());
}

$message = '';

// Handle Sign-Up
if (isset($_POST['signup'])) {
    $username = trim($_POST['username'] ?? '');
    $password = $_POST['password'] ?? '';
    $full_name = trim($_POST['full_name'] ?? '');

    if ($username && $password && $full_name) {
        // Check if username exists
        $stmt = $pdo->prepare("SELECT id FROM users WHERE username = ?");
        $stmt->execute([$username]);
        if ($stmt->fetch()) {
            $message = "Username already exists.";
        } else {
            $hash = password_hash($password, PASSWORD_DEFAULT);
            $stmt = $pdo->prepare("INSERT INTO users (username, password, full_name) VALUES (?, ?, ?)");
            $stmt->execute([$username, $hash, $full_name]);
            $message = "Account created! You can now log in.";
        }
    } else {
        $message = "Please fill in all fields.";
    }
}

// Handle Login
if (isset($_POST['login'])) {
    $username = trim($_POST['username'] ?? '');
    $password = $_POST['password'] ?? '';

    if ($username && $password) {
        $stmt = $pdo->prepare("SELECT * FROM users WHERE username = ?");
        $stmt->execute([$username]);
        $user = $stmt->fetch();
        if ($user && password_verify($password, $user['password'])) {
            $_SESSION['user'] = $user['full_name'];
            header("Location: dashboard.php"); // Redirect to a dashboard page
            exit;
        } else {
            $message = "Invalid username or password.";
        }
    } else {
        $message = "Please fill in all fields.";
    }
}
?>

<!DOCTYPE html>
<html lang="en">
<link rel="stylesheet" type="text/css" href="style.css">

<head>
<meta charset="UTF-8">
<title>Clash Royale Login/Signup</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
    body {
        font-family: Arial, sans-serif;
        background: #f4f4f4;
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
        margin: 0;
    }

    .container {
        background: #fff;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        width: 350px;
    }

    h1 {
        text-align: center;
        color: #1a3d5d;
        margin-bottom: 1rem;
    }

    form {
        display: flex;
        flex-direction: column;
    }

    input[type="text"], input[type="password"] {
        padding: 0.8rem;
        margin-bottom: 1rem;
        border-radius: 5px;
        border: 1px solid #ccc;
        font-size: 1rem;
    }

    input[type="submit"] {
        padding: 0.8rem;
        border-radius: 5px;
        border: none;
        background-color: #1a3d5d;
        color: #fff;
        font-weight: bold;
        cursor: pointer;
        transition: background 0.2s;
    }

    input[type="submit"]:hover {
        background-color: #274f70;
    }

    .message {
        margin-bottom: 1rem;
        color: red;
        font-weight: bold;
        text-align: center;
    }
</style>
</head>
<body>
<div class="container">
    <h1>Clash Royale Login/Signup</h1>
    <?php if($message): ?>
        <div class="message"><?= htmlspecialchars($message) ?></div>
    <?php endif; ?>

    <form method="post">
        <input type="text" name="username" placeholder="Username">
        <input type="password" name="password" placeholder="Password">
        <input type="text" name="full_name" placeholder="Full Name (for signup)">
        <input type="submit" name="signup" value="Sign Up">
        <input type="submit" name="login" value="Login">
    </form>
</div>
</body>
</html>

