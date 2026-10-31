# Fonia – Home Assistant Custom Component

[![GitHub Release](https://img.shields.io/github/v/release/LukaszP2/ha-fonia?style=flat-square)](https://github.com/LukaszP2/ha-fonia/releases)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg?style=flat-square)](https://hacs.xyz)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)


[![Otwórz repozytorium w HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=LukaszP2&repository=ha-fonia&category=integration)
[![Dodaj integrację do Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=fonia)

*(🇬🇧 English description below)*

---

## 🇵🇱 Opis

Nieoficjalna integracja z operatorem sieci komórkowej Fonia dla Home Assistant. Umożliwia monitorowanie pakietów danych, SMS, minut, stanu konta oraz aktywnych kart SIM i subskrypcji.

### Główne funkcje
- Monitorowanie pakietów internetowych (pozostały limit GB, data odnowienia)
- Licznik i stan minut oraz SMS/MMS
- Obsługa wielu kart SIM (Multi-SIM) w ramach jednego konta
- Stan konta i informacje o subskrypcji
- Diagnostyka i bezpieczne uwierzytelnianie

### Instalacja przez HACS (Niestandardowe repozytorium)

### 🚀 Szybka instalacja (1 kliknięcie przez My Home Assistant)

[![Otwórz repozytorium w HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=LukaszP2&repository=ha-fonia&category=integration)

Po zainstalowaniu i ponownym uruchomieniu Home Assistant, kliknij poniższy przycisk, aby skonfigurować integrację:

[![Dodaj integrację do Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=fonia)



1. Upewnij się, że masz zainstalowany **HACS** w Home Assistant.
2. W HACS przejdź do: **Integracje** -> menu w prawym górnym rogu (trzy kropki) -> **Niestandardowe repozytoria** (*Custom repositories*).
3. W polu **Repozytorium** wklej adres:
   ```text
   https://github.com/LukaszP2/ha-fonia
   ```
4. W polu **Kategoria** wybierz: **Integracja** (*Integration*).
5. Kliknij **Dodaj**, a następnie wyszukaj **Fonia** i kliknij **Pobierz**.
6. Uruchom ponownie Home Assistant.

### Konfiguracja

1. W Home Assistant przejdź do: **Ustawienia** -> **Urządzenia oraz usługi** -> **Dodaj integrację**.
2. Wyszukaj **Fonia**.
3. Postępuj zgodnie z instrukcjami na ekranie.

---

## 🇬🇧 Description

Unofficial Fonia mobile operator integration for Home Assistant. Monitors data packages, SMS, minutes, account balance, active SIM cards, and subscriptions.

### Installation via HACS (Custom Repository)

1. Open **HACS** in Home Assistant.
2. Navigate to **Integrations** -> top right menu (three dots) -> **Custom repositories**.
3. Enter repository URL:
   ```text
   https://github.com/LukaszP2/ha-fonia
   ```
4. Category: **Integration**.
5. Click **Add**, find **Fonia**, and install.
6. Restart Home Assistant.

---

## Licencja / License

Projekt objęty licencją [MIT](LICENSE).