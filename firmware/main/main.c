/*
 * firmware/main/main.c
 * ─────────────────────
 * WiFi CSI Home Sensing — ESP32 Firmware Skeleton
 *
 * What this will do (when complete):
 *   1. Connect to WiFi as a Station (STA)
 *   2. Enable CSI callback via esp_wifi_set_csi_rx_cb()
 *   3. Serialize each CSI frame and transmit over UDP to the sensor-backend
 *
 * Currently: skeleton only — WiFi init + UDP socket setup stub.
 *
 * Build:  idf.py build
 * Flash:  idf.py -p COM<N> flash monitor
 */

#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "lwip/sockets.h"

/* ── Configuration (move to sdkconfig / menuconfig later) ─────────────────── */
#define WIFI_SSID      "YOUR_SSID"
#define WIFI_PASS      "YOUR_PASSWORD"
#define BACKEND_IP     "192.168.1.100"   // IP of the machine running sensor-backend
#define BACKEND_PORT   5005              // UDP port the backend listens on
#define NODE_ID        "esp32-node-01"   // Unique ID for this sensor node

static const char *TAG = "wifi-csi";

/* ── WiFi event handler ───────────────────────────────────────────────────── */
static void wifi_event_handler(void *arg, esp_event_base_t base,
                               int32_t id, void *data)
{
    if (base == WIFI_EVENT && id == WIFI_EVENT_STA_START) {
        ESP_LOGI(TAG, "Connecting to WiFi…");
        esp_wifi_connect();
    } else if (base == WIFI_EVENT && id == WIFI_EVENT_STA_DISCONNECTED) {
        ESP_LOGW(TAG, "WiFi disconnected — retrying…");
        esp_wifi_connect();
    } else if (base == IP_EVENT && id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t *event = (ip_event_got_ip_t *)data;
        ESP_LOGI(TAG, "Got IP: " IPSTR, IP2STR(&event->ip_info.ip));
        // TODO: open UDP socket to BACKEND_IP:BACKEND_PORT here
    }
}

/* ── CSI receive callback (stub) ──────────────────────────────────────────── */
static void csi_rx_callback(void *ctx, wifi_csi_info_t *info)
{
    /*
     * TODO:
     *   1. Serialize info->buf (raw CSI bytes) + info->rx_ctrl (RSSI, noise)
     *   2. Prepend NODE_ID + timestamp
     *   3. sendto() over UDP to sensor-backend
     */
    ESP_LOGD(TAG, "CSI frame received — rssi=%d, len=%d",
             info->rx_ctrl.rssi, info->len);
}

/* ── WiFi init ────────────────────────────────────────────────────────────── */
static void wifi_init_sta(void)
{
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));

    ESP_ERROR_CHECK(esp_event_handler_instance_register(
        WIFI_EVENT, ESP_EVENT_ANY_ID, &wifi_event_handler, NULL, NULL));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(
        IP_EVENT, IP_EVENT_STA_GOT_IP, &wifi_event_handler, NULL, NULL));

    wifi_config_t wifi_cfg = {
        .sta = {
            .ssid     = WIFI_SSID,
            .password = WIFI_PASS,
        },
    };
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_cfg));
    ESP_ERROR_CHECK(esp_wifi_start());
}

/* ── CSI init (stub) ──────────────────────────────────────────────────────── */
static void csi_init(void)
{
    wifi_csi_config_t csi_cfg = {
        .lltf_en           = true,
        .htltf_en          = true,
        .stbc_htltf2_en    = true,
        .ltf_merge_en      = true,
        .channel_filter_en = true,
        .manu_scale        = false,
    };
    ESP_ERROR_CHECK(esp_wifi_set_csi_config(&csi_cfg));
    ESP_ERROR_CHECK(esp_wifi_set_csi_rx_cb(&csi_rx_callback, NULL));
    ESP_ERROR_CHECK(esp_wifi_set_csi(true));
    ESP_LOGI(TAG, "CSI enabled");
}

/* ── Main ─────────────────────────────────────────────────────────────────── */
void app_main(void)
{
    ESP_LOGI(TAG, "WiFi CSI Node starting — ID: %s", NODE_ID);

    ESP_ERROR_CHECK(nvs_flash_init());
    wifi_init_sta();

    // CSI can only be enabled after WiFi starts
    // TODO: enable csi_init() after WiFi STA connects
    // csi_init();

    ESP_LOGI(TAG, "Skeleton running — awaiting WiFi connection…");
}
