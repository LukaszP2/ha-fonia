# Fonia – Home Assistant Custom Component

[![GitHub Release](https://img.shields.io/github/v/release/LukaszP2/ha-fonia?style=flat-square)](https://github.com/LukaszP2/ha-fonia/releases)
[![Home Assistant Marketplace](https://img.shields.io/badge/HA-Marketplace-blue.svg?style=flat-square)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=LukaszP2&repository=ha-fonia&category=integration)
[![Languages: EN | PL](https://img.shields.io/badge/Languages-EN%20%7C%20PL-orange.svg?style=flat-square)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)

[![Open repository in Home Assistant Marketplace](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=LukaszP2&repository=ha-fonia&category=integration)
[![Add Integration to Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=fonia)

*(🇵🇱 Polska wersja opisu znajduje się poniżej)*

---

## 🇬🇧 Description

Unofficial **Fonia** mobile operator integration for Home Assistant. It monitors domestic and EU roaming data packages, SIM card status, subscription renewal dates and prices, cashback balance, and provides a manual data usage synchronization trigger.

### Key Features

- **Data Package Tracking**: Remaining domestic and EU roaming data (GB), total package limits, and percentage of used data.
- **Subscription & Billing**: SIM card active status, next subscription renewal date, price in PLN, and order count.
- **Cashback Monitoring**: Current cashback account balance and available/spendable cashback amount.
- **Multi-SIM Support**: Automatically creates an account device and dedicated sub-devices for each SIM card on your account.
- **Data Usage Sync Button**: Dedicated button entity to request an on-demand data usage synchronization directly from the operator billing engine.
- **Flexible Options**: Custom account name, customizable scan interval (5–60 minutes), optional background usage sync toggle, and category filtering (Payments, Usage, History, Advanced).
- **Diagnostics & Security**: Secure credential handling with automatic re-authentication flow, reconfiguration support, and redacted diagnostics export.
- **Automated Blueprint Deployment**: Pre-built automation blueprints deployed straight to your Home Assistant instance upon setup.
- **Multi-language Support (EN / PL)**: Fully localized into English and Polish across all entity names, device names, configuration flows, options, and error messages.

*(Note: Voice call minutes and SMS/MMS counters are not exposed by the operator's web API. They will be integrated if made available in the future.)*

---

### Installation via Home Assistant Marketplace

#### 🚀 1-Click Fast Installation (My Home Assistant)

Click the button below to add this repository directly to your Home Assistant Marketplace:

[![Open repository in Home Assistant Marketplace](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=LukaszP2&repository=ha-fonia&category=integration)

After downloading the component and restarting Home Assistant, click below to set up the integration:

[![Add Integration to Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=fonia)

#### 🛠️ Manual Installation (Marketplace)

1. In Home Assistant, open **Settings** > **Marketplace** (or your sidebar **Marketplace**).
2. Click the three dots menu (⋮) in the top-right corner and select **Custom repositories**.
3. In the **Repository** field, enter:
   ```text
   https://github.com/LukaszP2/ha-fonia
   ```
4. In the **Category** dropdown, select **Integration**.
5. Click **Add**, find **Fonia**, and click **Download**.
6. Restart Home Assistant.

> [!NOTE]
> **For older Home Assistant versions (< 2026.11 / legacy HACS):**
> Open **HACS** > **Integrations** > three dots (⋮) > **Custom repositories**, enter the repository URL above with category **Integration**, and download.

---

### Configuration & Options

1. In Home Assistant, navigate to **Settings** > **Devices & services** > **Add integration**.
2. Search for **Fonia**.
3. Enter your login credentials for `moja.fonia.app` (username / email and password). You can optionally provide a custom display name.
4. Once added, you can adjust settings anytime by clicking **Configure**:
   - **Custom Name**: Rename the integration instance.
   - **Refresh Interval**: Polling frequency from 5 to 60 minutes (default: 15 minutes).
   - **Automatic Usage Sync**: Toggle periodic usage synchronization (runs every 2 hours).
   - **Categories**: Enable or disable entity groups (*Payments & billing*, *Usage statistics*, *Transaction history*, *Advanced diagnostics*).

---

### 📋 Automation Blueprints

Fonia includes 4 pre-configured automation blueprints. They are automatically copied to your `/config/blueprints/automation/fonia/` folder when the integration loads, or you can import them into Home Assistant with one click using the badges below:

#### 1. Low Domestic Data Warning
Notifies your mobile device when domestic remaining data (GB) falls below a chosen threshold, showing remaining GB and optional percentage.

[![Import Low Data Warning Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FLukaszP2%2Fha-fonia%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Ffonia%2Flow_data_warning.yaml)

#### 2. Roaming Data Warning (EU)
Sends a high-priority alert to your phone when EU roaming data drops below a safe limit to prevent unexpected charges.

[![Import Roaming Data Warning Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FLukaszP2%2Fha-fonia%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Ffonia%2Froaming_data_warning.yaml)

#### 3. Subscription Renewal Reminder
Checks your next payment date daily and sends an advance reminder (e.g. 3 days before and/or 1 day before) with the renewal amount so you have funds on your payment card.

[![Import Subscription Renewal Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FLukaszP2%2Fha-fonia%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Ffonia%2Fsubscription_renewal.yaml)

#### 4. Cashback Change Alert
Sends an immediate notification whenever your cashback balance changes, reporting both the delta (+/- amount) and the new total balance.

[![Import Cashback Change Alert Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FLukaszP2%2Fha-fonia%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Ffonia%2Fcashback_change_alert.yaml)

---

### Provided Entities

| Entity Type | Entity Name / Key | Description | Category / Scope |
| :--- | :--- | :--- | :--- |
| **Sensor** | `data_remaining` | Remaining domestic data allowance (GB) | Core (SIM) |
| **Sensor** | `data_total` | Total domestic data allowance (GB) *(disabled by default)* | Usage / Diagnostic (SIM) |
| **Sensor** | `data_used_percentage` | Percentage of domestic data used (%) | Usage (SIM) |
| **Sensor** | `roaming_data_remaining` | Remaining EU roaming data (GB) | Usage (SIM) |
| **Sensor** | `roaming_data_total` | Total EU roaming package (GB) *(disabled by default)* | Usage / Diagnostic (SIM) |
| **Sensor** | `roaming_data_used_percentage`| Percentage of EU roaming data used (%) | Usage (SIM) |
| **Sensor** | `status` | SIM / subscription status (active, pending, etc.) | Core (SIM) |
| **Sensor** | `next_payment` | Next subscription renewal date | Payments (SIM) |
| **Sensor** | `renewal_price` | Next renewal charge amount (PLN) | Payments (SIM) |
| **Sensor** | `order_count` | Number of orders on subscription *(disabled by default)* | Payments / Diagnostic (SIM) |
| **Sensor** | `cashback_balance` | Total cashback balance (PLN) | Core (Account) |
| **Sensor** | `cashback_spendable` | Available / spendable cashback (PLN) | Core (Account) |
| **Sensor** | `cashback_transaction_count` | Total cashback transactions *(disabled by default)* | History / Diagnostic (Account) |
| **Sensor** | `site_alert_count` | Number of operator announcements *(disabled by default)*| Advanced / Diagnostic (Account) |
| **Button** | `usage_sync` | Triggers immediate usage synchronization from Fonia | Button (Account) |

---

### ❓ Frequently Asked Questions (FAQ)

**What happens if a phone number or SIM card is cancelled or replaced?**  
The entities associated with the inactive SIM card will transition to the `unavailable` state. This is intentional to preserve your historical recorder statistics and long-term data charts. If you wish to permanently remove the inactive device from Home Assistant:
1. Navigate to **Settings** > **Devices & services** > **Devices**.
2. Select the inactive Fonia SIM device (e.g. `Fonia · +48...`).
3. Click the three dots menu (⋮) in the top-right corner of the device card and select **Delete**.

---

## 🇵🇱 Opis

Nieoficjalna integracja z operatorem sieci komórkowej **Fonia** dla Home Assistant. Umożliwia monitorowanie pakietów danych krajowych i roamingu UE, statusu kart SIM, dat odnowienia subskrypcji i cen, salda cashback oraz ręczną synchronizację danych zużycia.

### Główne funkcje

- **Monitorowanie transferu danych**: Pozostały limit danych w kraju i roamingu UE (w GB), wielkość całego pakietu oraz procentowe zużycie.
- **Subskrypcje i finanse**: Status aktywności numeru, data kolejnej płatności, kwota odnowienia w PLN oraz liczba zamówień.
- **Obsługa Cashback**: Bieżące saldo środków cashback oraz kwota dostępna do wykorzystania.
- **Obsługa Multi-SIM**: Automatyczne tworzenie urządzenia nadrzędnego konta oraz oddzielnych urządzeń dla każdej karty SIM przypisanej do profilu.
- **Przycisk synchronizacji danych**: Przycisk wyzwalający wymuszenie natychmiastowego pobrania świeżych liczników z systemu bilingowego operatora.
- **Elastyczne opcje**: Własna nazwa instancji, konfigurowalny interwał odpytywania (5–60 minut), opcjonalna automatyczna synchronizacja zużycia (co 2 godziny) oraz filtrowanie kategorii encji (Płatności, Zużycie, Historia, Zaawansowane).
- **Diagnostyka i bezpieczeństwo**: Bezpieczne przechowywanie danych logowania, obsługa ponownego uwierzytelnienia (reauth), rekonfiguracji oraz eksport zanonimizowanej diagnostyki.
- **Automatyczne wdrażanie blueprintów**: Gotowe szablony automatyzacji są kopiowane do instancji Home Assistant zaraz po uruchomieniu integracji.
- **Wersje językowe (PL / EN)**: Pełne tłumaczenie na język polski i angielski dla wszystkich encji, urządzeń, formularzy konfiguracji, opcji oraz komunikatów błędów.

*(Uwaga: liczniki minut oraz SMS/MMS nie są udostępniane przez interfejs webowy operatora. Zostaną dodane, jeśli operator udostępni je w przyszłości.)*

---

### Instalacja przez Home Assistant Marketplace

#### 🚀 Szybka instalacja (1 kliknięcie przez My Home Assistant)

Kliknij poniższy przycisk, aby dodać repozytorium do Home Assistant Marketplace:

[![Otwórz repozytorium w Home Assistant Marketplace](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=LukaszP2&repository=ha-fonia&category=integration)

Po pobraniu i ponownym uruchomieniu Home Assistant, kliknij poniższy przycisk, aby skonfigurować integrację:

[![Dodaj integrację do Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=fonia)

#### 🛠️ Instalacja ręczna (Marketplace)

1. W Home Assistant przejdź do: **Ustawienia** > **Marketplace** (lub wybierz **Marketplace** z menu bocznego).
2. Kliknij ikonę trzech kropek (⋮) w prawym górnym rogu i wybierz **Niestandardowe repozytoria** (*Custom repositories*).
3. W polu **Repozytorium** wklej adres:
   ```text
   https://github.com/LukaszP2/ha-fonia
   ```
4. W polu **Kategoria** wybierz: **Integracja** (*Integration*).
5. Kliknij **Dodaj**, wyszukaj **Fonia** i kliknij **Pobierz**.
6. Uruchom ponownie Home Assistant.

> [!NOTE]
> **Dla starszych wersji Home Assistant (< 2026.11 / klasyczny HACS):**
> Otwórz **HACS** > **Integracje** > trzy kropki (⋮) > **Niestandardowe repozytoria**, wklej powyższy adres jako **Integracja** i kliknij Pobierz.

---

### Konfiguracja i opcje

1. W Home Assistant przejdź do: **Ustawienia** > **Urządzenia oraz usługi** > **Dodaj integrację**.
2. Wyszukaj **Fonia**.
3. Wprowadź login (lub e-mail) oraz hasło do panelu `moja.fonia.app`. Opcjonalnie możesz podać własną nazwę wyświetlaną.
4. Po dodaniu możesz w każdej chwili zmienić parametry pracy, klikając **Konfiguruj** na kafelku integracji:
   - **Własna nazwa**: zmiana wyświetlanej nazwy integracji.
   - **Interwał odświeżania**: częstotliwość odpytywania API w minutach (od 5 do 60 min, domyślnie 15 min).
   - **Automatyczna synchronizacja zużycia**: włączenie/wyłączenie odświeżania bilingowego co 2 godziny.
   - **Kategorie encji**: włączanie lub wyłączanie grup sensorów (*Płatności i rozliczenia*, *Statystyki zużycia*, *Historia transakcji*, *Zaawansowana diagnostyka*).

---

### 📋 Gotowe Blueprinty automatyzacji

W repozytorium przygotowano 4 gotowe blueprinty automatyzacji. Są one automatycznie wgrywane do katalogu `/config/blueprints/automation/fonia/` przy starcie integracji, a także można je zaimportować 1 kliknięciem za pomocą poniższych przycisków:

#### 1. Alert o wyczerpywaniu pakietu internetu
Wysyła powiadomienie na aplikację mobilną, gdy transfer danych w kraju spadnie poniżej ustalonego progu (GB), podając pozostały limit oraz opcjonalnie procent zużycia.

[![Zaimportuj blueprint Alert o wyczerpywaniu pakietu](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FLukaszP2%2Fha-fonia%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Ffonia%2Flow_data_warning.yaml)

#### 2. Alert o wyczerpywaniu roamingu (UE)
Wysyła ostrzeżenie o wysokim priorytecie na telefon, gdy transfer w roamingu UE zbliża się do wyczerpania, zapobiegając naliczeniu dodatkowych opłat.

[![Zaimportuj blueprint Alert roamingowy](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FLukaszP2%2Fha-fonia%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Ffonia%2Froaming_data_warning.yaml)

#### 3. Przypomnienie o płatności subskrypcji
Sprawdza codziennie termin kolejnej płatności i wysyła przypomnienie z wyprzedzeniem (np. 3 dni i/lub 1 dzień przed) z informacją o kwocie do pobrania.

[![Zaimportuj blueprint Przypomnienie o płatności](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FLukaszP2%2Fha-fonia%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Ffonia%2Fsubscription_renewal.yaml)

#### 4. Powiadomienie o zmianie kwoty cashback
Wysyła natychmiastowe powiadomienie o każdej zmianie salda cashback (nowy zwrot lub wykorzystanie środków) z informacją o różnicy kwoty i bieżącym saldzie.

[![Zaimportuj blueprint Powiadomienie o cashbacku](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2FLukaszP2%2Fha-fonia%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Ffonia%2Fcashback_change_alert.yaml)

---

### Dostępne encje

| Typ encji | Klucz / Nazwa | Opis | Kategoria / Urządzenie |
| :--- | :--- | :--- | :--- |
| **Sensor** | `data_remaining` | Pozostały limit danych w kraju (GB) | Główne (Karta SIM) |
| **Sensor** | `data_total` | Łączny pakiet danych w kraju (GB) *(domyślnie wyłączony)* | Zużycie / Diagnostyka (Karta SIM) |
| **Sensor** | `data_used_percentage` | Procentowe wykorzystanie danych w kraju (%) | Zużycie (Karta SIM) |
| **Sensor** | `roaming_data_remaining` | Pozostały pakiet danych w roamingu UE (GB) | Zużycie (Karta SIM) |
| **Sensor** | `roaming_data_total` | Całkowity pakiet roamingu UE (GB) *(domyślnie wyłączony)* | Zużycie / Diagnostyka (Karta SIM) |
| **Sensor** | `roaming_data_used_percentage`| Procentowe wykorzystanie roamingu UE (%) | Zużycie (Karta SIM) |
| **Sensor** | `status` | Status numeru / subskrypcji (aktywna, oczekująca itp.) | Główne (Karta SIM) |
| **Sensor** | `next_payment` | Data następnej płatności za subskrypcję | Płatności (Karta SIM) |
| **Sensor** | `renewal_price` | Koszt kolejnego odnowienia (PLN) | Płatności (Karta SIM) |
| **Sensor** | `order_count` | Liczba zamówień subskrypcji *(domyślnie wyłączony)* | Płatności / Diagnostyka (Karta SIM) |
| **Sensor** | `cashback_balance` | Całkowite saldo cashback (PLN) | Główne (Konto Fonia) |
| **Sensor** | `cashback_spendable` | Dostępne środki cashback do wypłaty (PLN) | Główne (Konto Fonia) |
| **Sensor** | `cashback_transaction_count` | Liczba transakcji cashback *(domyślnie wyłączony)* | Historia / Diagnostyka (Konto Fonia) |
| **Sensor** | `site_alert_count` | Liczba komunikatów operatora *(domyślnie wyłączony)* | Zaawansowane / Diagnostyka (Konto Fonia) |
| **Przycisk**| `usage_sync` | Wymuszenie synchronizacji zużycia danych z Fonia | Przycisk (Konto Fonia) |

---

### ❓ Często zadawane pytania (FAQ)

**Co się dzieje po rezygnacji z numeru lub wymianie karty SIM?**  
Encje przypisane do nieaktywnej karty przechodzą w stan `Niedostępny` (`unavailable`). Jest to zamierzone działanie Home Assistant mające na celu ochronę danych historycznych i statystyk w bazie Recorder. Jeśli chcesz trwale usunąć nieaktywny numer z Home Assistant:
1. Przejdź do: **Ustawienia** > **Urządzenia oraz usługi** > **Urządzenia**.
2. Wybierz nieaktywne urządzenie Fonia (np. `Fonia · +48...`).
3. Kliknij menu w prawym górnym rogu karty urządzenia (trzy kropki ⋮) i wybierz **Usuń**.

---

## Licencja / License

Projekt objęty licencją [MIT](LICENSE).
