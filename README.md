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
- Monitorowanie pakietów internetowych (pozostały limit GB, pakiety roamingowe, procent zużycia)
- Stan aktywności kart SIM, subskrypcji oraz data odnowienia i cena
- Obsługa wielu kart SIM (Multi-SIM) w ramach jednego konta
- Stan konta cashback oraz alerty systemowe Fonia
- Przycisk ręcznej synchronizacji zużycia danych
- Diagnostyka i bezpieczne uwierzytelnianie
*(Uwaga: liczniki minut oraz SMS/MMS zostaną dodane w przyszłych wydaniach, jeśli operator udostępni je w API)*

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

### 📋 Gotowe Blueprinty automatyzacji

W repozytorium przygotowane są gotowe blueprinty automatyzacji (w katalogu `blueprints/automation/fonia/`):
- **Alert o wyczerpywaniu pakietu internetu** (`low_data_warning.yaml`) – powiadamia, gdy transfer danych w kraju spadnie poniżej ustalonego progu (GB).
- **Alert o wyczerpywaniu roamingu (UE)** (`roaming_data_warning.yaml`) – ostrzega o wyczerpującym się pakiecie danych w roamingu.
- **Przypomnienie o płatności subskrypcji** (`subscription_renewal.yaml`) – powiadomienie przed pobraniem środków z karty (np. 3 dni i/lub 1 dzień przed terminem odnowienia).
- **Powiadomienie o zmianie kwoty cashback** (`cashback_change_alert.yaml`) – powiadamia o naliczeniu lub wykorzystaniu środków cashback oraz bieżącym saldzie.

---

## 🇬🇧 Description

Unofficial Fonia mobile operator integration for Home Assistant. Monitors data packages, roaming data, active SIM cards, subscriptions, and cashback balance.

### Key features
- Mobile data monitoring (remaining GB, roaming data, percentage used)
- SIM card status, subscription renewal date, and price
- Multi-SIM support under a single account
- Cashback balance and Fonia alerts
- Manual usage synchronization button
- Diagnostics and secure authentication
*(Note: call minutes and SMS/MMS counters will be added in future releases if made available by the operator API)*

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

### 📋 Ready-to-use Automation Blueprints

Available in `blueprints/automation/fonia/`:
- **Low Data Warning** (`low_data_warning.yaml`) – notifies when domestic data (GB) drops below threshold.
- **Roaming Data Warning** (`roaming_data_warning.yaml`) – alerts when EU roaming data is running low.
- **Subscription Renewal Reminder** (`subscription_renewal.yaml`) – reminds before subscription renewal and card charge.
- **Cashback Change Alert** (`cashback_change_alert.yaml`) – notifies about new cashback earnings or redemptions.

---

## Licencja / License

Projekt objęty licencją [MIT](LICENSE).