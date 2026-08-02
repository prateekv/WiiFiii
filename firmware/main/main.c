#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "esp_netif.h"
#include "lwip/sockets.h"
#include "lwip/netdb.h"

/* ── Configuration ───────────────────────────────────────────────────────── */
/* ENTER YOUR REAL WIFI DETAILS HERE BEFORE FLASHING */
#define WIFI_SSID      "YOUR_WIFI_NAME"
#define WIFI_PASS      "YOUR_WIFI_PASSWORD"

#define NODE_ID        "esp32-node-01"

static const char *TAG = "wifi-csi";
static bool wifi_connected = false;

/* ── Active Traffic Generator ───────────────────────────────────────────────
 * WiFi CSI requires packets to travel through the air. Routers send beacons
 * every ~100ms, but to get a smooth live stream, we actively transmit UDP 
 * packets. The router's responses/ACKs will generate rich CSI data.
 */
static void traffic_generator_task(void *pvParameters)
{
    ESP_LOGI(TAG, "Traffic generator task started.");
    while (!wifi_connected) {
        vTaskDelay(pdMS_TO_TICKS(500));
    }

    // Create a dummy UDP socket to send broadcast packets
    int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_IP);
    if (sock < 0) {
        ESP_LOGE(TAG, "Unable to create socket");
        vTaskDelete(NULL);
    }

    struct sockaddr_in dest_addr;
    dest_addr.sin_family = AF_INET;
    dest_addr.sin_port = htons(5555);
    dest_addr.sin_addr.s_addr = inet_addr("255.255.255.255"); // Broadcast

    const char *payload = "CSI_PING";

    while (1) {
        if (wifi_connected) {
            sendto(sock, payload, strlen(payload), 0, 
                   (struct sockaddr *)&dest_addr, sizeof(dest_addr));
        }
        // Send a packet every 50ms (20 packets/sec)
        vTaskDelay(pdMS_TO_TICKS(50));
    }
}

/* ── CSI Receive Callback ───────────────────────────────────────────────────
 * This function is called directly by the WiFi driver every time a packet 
 * containing CSI data is received.
 */
static void csi_rx_callback(void *ctx, wifi_csi_info_t *info)
{
    if (!info || !info->buf) {
        return;
    }

    // info->mac is the sender's MAC address (usually the router)
    const uint8_t *mac = info->mac;
    
    // info->rx_ctrl contains metadata like RSSI (signal strength)
    int8_t rssi = info->rx_ctrl.rssi;
    
    // info->buf contains the raw complex numbers (I/Q) for the subcarriers
    uint16_t len = info->len;

    // Print a cleanly formatted summary to the Serial Monitor
    ESP_LOGI(TAG, "[CSI] MAC: %02x:%02x:%02x:%02x:%02x:%02x | RSSI: %3d dBm | Bytes: %3d | First 4 bytes: %02x %02x %02x %02x",
             mac[0], mac[1], mac[2], mac[3], mac[4], mac[5],
             rssi, len,
             info->buf[0], info->buf[1], info->buf[2], info->buf[3]);
}

/* ── WiFi Event Handler ───────────────────────────────────────────────────── */
static void wifi_event_handler(void *arg, esp_event_base_t base,
                               int32_t id, void *data)
{
    if (base == WIFI_EVENT && id == WIFI_EVENT_STA_START) {
        ESP_LOGI(TAG, "Connecting to WiFi…");
        esp_wifi_connect();
    } else if (base == WIFI_EVENT && id == WIFI_EVENT_STA_DISCONNECTED) {
        wifi_connected = false;
        ESP_LOGW(TAG, "WiFi disconnected — retrying…");
        esp_wifi_connect();
    } else if (base == IP_EVENT && id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t *event = (ip_event_got_ip_t *)data;
        ESP_LOGI(TAG, "Got IP: " IPSTR, IP2STR(&event->ip_info.ip));
        wifi_connected = true;
    }
}

/* ── Main Application ─────────────────────────────────────────────────────── */
void app_main(void)
{
    ESP_LOGI(TAG, "=========================================");
    ESP_LOGI(TAG, "   WiiFiii CSI Node Starting             ");
    ESP_LOGI(TAG, "   Node ID: %s                           ", NODE_ID);
    ESP_LOGI(TAG, "=========================================");

    // 1. Initialize NVS (required for WiFi)
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
      ESP_ERROR_CHECK(nvs_flash_erase());
      ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    // 2. Initialize WiFi Station
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    // Enable CSI in the WiFi driver configuration
    cfg.csi_enable = 1; 
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

    // 3. Configure and Enable CSI
    wifi_csi_config_t csi_cfg = {
        .lltf_en           = true,
        .htltf_en          = true,
        .stbc_htltf2_en    = true,
        .ltf_merge_en      = true,
        .channel_filter_en = true,
        .manu_scale        = false,
        .shift             = false
    };
    ESP_ERROR_CHECK(esp_wifi_set_csi_config(&csi_cfg));
    ESP_ERROR_CHECK(esp_wifi_set_csi_rx_cb(&csi_rx_callback, NULL));
    ESP_ERROR_CHECK(esp_wifi_set_csi(true));
    ESP_LOGI(TAG, "CSI collection successfully enabled!");

    // 4. Start the traffic generator to ensure we get plenty of packets
    xTaskCreate(traffic_generator_task, "traffic_gen", 4096, NULL, 5, NULL);
}
