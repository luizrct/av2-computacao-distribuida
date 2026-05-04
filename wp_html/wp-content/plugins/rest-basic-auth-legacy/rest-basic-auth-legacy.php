<?php
/**
 * Plugin Name: REST Basic Auth Legacy
 * Description: Habilita autenticação Basic Auth para WP REST API em versões legadas.
 * Version: 1.0.0
 * Author: Projeto AV2
 */

if (!defined('ABSPATH')) {
    exit;
}

/**
 * Autentica requisições da REST API usando Authorization: Basic.
 * ATENCAO: use apenas em ambiente de teste/laboratorio.
 */
function rest_basic_auth_legacy_determine_user($user_id) {
    if (!empty($user_id)) {
        return $user_id;
    }

    if (!defined('REST_REQUEST') || !REST_REQUEST) {
        return $user_id;
    }

    $username = null;
    $password = null;

    if (isset($_SERVER['PHP_AUTH_USER'])) {
        $username = $_SERVER['PHP_AUTH_USER'];
    }
    if (isset($_SERVER['PHP_AUTH_PW'])) {
        $password = $_SERVER['PHP_AUTH_PW'];
    }

    if ($username === null || $password === null) {
        return $user_id;
    }

    $user = wp_authenticate($username, $password);
    if (is_wp_error($user)) {
        return $user_id;
    }

    return $user->ID;
}
add_filter('determine_current_user', 'rest_basic_auth_legacy_determine_user', 20);

