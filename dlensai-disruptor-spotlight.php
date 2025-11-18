<?php
/**
 * Plugin Name: DLENSAI Disruptor Spotlight
 * Description: Embeds the DLENS AI Spotlight Generator inside WordPress using an iframe.
 * Version: 1.0
 * Author: DLENS AI
 */

if (!defined('ABSPATH')) {
    exit; // No direct access
}

// -----------------------------------------------------------
// Shortcode to embed the Spotlight Generator
// -----------------------------------------------------------
function dlensai_disruptor_spotlight_embed() {

    $backend_url = "http://localhost:5000"; // Your Flask app URL

    ob_start();
    ?>

    <div style="width:100%; max-width:1200px; margin:auto; text-align:center;">
        <iframe 
            src="<?php echo esc_url($backend_url); ?>" 
            style="width:100%; height:900px; border:none; border-radius:12px; overflow:hidden;"
            allowfullscreen
            loading="lazy">
        </iframe>
    </div>

    <style>
        /* Mobile responsive iframe */
        @media (max-width: 768px) {
            iframe {
                height: 1000px !important;
            }
        }
    </style>

    <?php
    return ob_get_clean();
}

add_shortcode("dlensai-disruptor-spotlight", "dlensai_disruptor_spotlight_embed");


// -----------------------------------------------------------
// Optional: Auto-create a WordPress page with this slug
// -----------------------------------------------------------
function dlensai_disruptor_create_page() {

    $slug = "dlensai-disruptor-spotlight";

    // Page already exists?
    $existing_page = get_page_by_path($slug);
    if ($existing_page) {
        return;
    }

    // Create custom page
    wp_insert_post([
        "post_title"   => "DLENS Disruptor Spotlight",
        "post_name"    => $slug,
        "post_status"  => "publish",
        "post_type"    => "page",
        "post_content" => "[dlensai-disruptor-spotlight]",
    ]);
}
register_activation_hook(__FILE__, "dlensai_disruptor_create_page");
