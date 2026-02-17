if (typeof translations === 'undefined') var translations = {};

translations.pl = {
    title: "Sprawdzanie kompatybilności modów Minecraft",
    subtitle: "Sprawdź kompatybilność swoich modów z wersją serwera Minecraft",
    current_mc_version: "Aktualna wersja MC",
    latest_official: "Najnowsza oficjalna",
    background_check_status: "Status sprawdzania w tle",
    tracked_mods: "Śledzone mody",
    compatible_mods: "Kompatybilne mody",
    not_set: "Nie ustawiono",
    checking: "Sprawdzanie...",
    last_check: "Ostatnio: {time}",
    next_check: "Następne: {time}",
    never: "Nigdy",
    tabs: {
        results: "Wyniki kompatybilności",
        add_mod: "Dodaj moda",
        versions: "Zarządzaj wersjami",
        import_export: "Eksport/Import",
        logs: "Logi zadań w tle"
    },
    add_mod_panel: {
        title: "Dodaj moda do śledzenia",
        slug_label: "Slug moda (z Modrinth)",
        slug_placeholder: "np. sodium, lithium, iris",
        type_label: "Preferowany typ",
        type_both: "Oba (Klient + Serwer)",
        type_client: "Tylko klient",
        type_server: "Tylko serwer",
        channel_label: "Kanał stabilności",
        channel_stable: "Tylko stabilne wydania",
        channel_beta: "Uwzględnij wersje Beta",
        channel_alpha: "Uwzględnij wersje Alpha",
        add_btn: "Dodaj moda",
        list_title: "Śledzone mody",
        empty: "Brak śledzonych modów"
    },
    manage_versions_panel: {
        title: "Zarządzaj wersjami Minecraft",
        version_label: "Wersja (np. 1.21.1)",
        version_placeholder: "1.21.1",
        loader_label: "Loader",
        type_label: "Typ",
        type_release: "Wydanie",
        type_snapshot: "Snapshot",
        set_current_label: "Ustaw jako aktualną wersję serwera",
        add_btn: "Dodaj wersję",
        list_title: "Lista wersji",
        empty: "Brak dodanych wersji"
    },
    import_export_panel: {
        title: "Eksport / Import",
        description: "Zarządzaj swoją listą modów używając formatu Docker Compose (styl itzg/minecraft-server).",
        export_version_label: "Wybierz wersję Minecraft do eksportu",
        no_compatible_versions: "Nie znaleziono kompatybilnych wersji",
        export_hint: "Pokazywane są tylko wersje, w których wszystkie mody serwerowe/oba są kompatybilne (mody tylko klienckie są ignorowane).",
        yaml_label: "Compose YAML / MODRINTH_PROJECTS",
        yaml_placeholder: "Wklej tutaj swój docker-compose.yml...",
        export_btn: "Eksportuj aktualne",
        import_btn: "Importuj z powyższego"
    },
    results_panel: {
        filter_version_label: "Filtruj według wersji Minecraft",
        all_versions: "Wszystkie wersje",
        filter_type_label: "Filtruj według typu moda",
        all_types: "Wszystkie typy",
        type_server: "Strona serwera (Serwer + Oba)",
        type_client: "Strona klienta (Klient + Oba)",
        type_both: "Tylko oba",
        empty: "Dodaj mody, aby zobaczyć wyniki kompatybilności",
        empty_filter: "Nie znaleziono wyników kompatybilności dla wybranych filtrów."
    },
    logs_panel: {
        waiting: "Oczekiwanie na logi zadań w tle...",
        no_logs: "Brak logów. Zadanie w tle wkrótce się rozpocznie..."
    },
    badges: {
        server: "Serwer",
        client: "Klient",
        current: "Aktualna"
    },
    mod_item: {
        supports: "Obsługuje: {client} | {server}",
        no_client: "Brak klienta",
        no_server: "Brak serwera",
        remove_btn: "Usuń"
    },
    version_item: {
        unknown_date: "Nieznana data",
        set_current_btn: "Ustaw jako aktualną",
        delete_btn: "Usuń",
        delete_confirm: "Czy na pewno chcesz usunąć tę wersję? Wszystkie powiązane wyniki kompatybilności zostaną utracone."
    },
    results_item: {
        mod_version: "Wersja moda:",
        unknown: "Nieznana"
    },
    status: {
        compatible: "Kompatybilny",
        incompatible: "Niekompatybilny",
        error: "Błąd"
    },
    toasts: {
        failed_load: "Błąd podczas ładowania danych początkowych",
        enter_version: "Proszę podać wersję",
        version_added: "Wersja dodana. Odświeżanie...",
        current_updated: "Aktualna wersja zaktualizowana",
        version_deleted: "Wersja usunięta",
        enter_slug: "Proszę podać slug moda",
        mod_added: "Mod dodany pomyślnie",
        side_updated: "Strona moda zaktualizowana",
        channel_updated: "Kanał moda zaktualizowany",
        mod_removed: "Mod usunięty",
        failed_remove: "Nie udało się usunąć moda",
        select_export_version: "Proszę wybrać kompatybilną wersję do eksportu",
        exported_clipboard: "Wyeksportowano i skopiowano do schowka!",
        exported_no_clipboard: "Wyeksportowano! (Schowek nie jest obsługiwany w tej przeglądarce/kontekście)",
        exported_manual: "Wyeksportowano! (Wymagane ręczne kopiowanie)",
        paste_yaml: "Proszę najpierw wkleić treść YAML",
        import_success: "Pomyślnie zaimportowano {count} nowych modów!"
    },
    log_patterns: [
        { pattern: /Database empty\. Importing latest version: (.+) \((.+)\)/, replacement: "Baza danych pusta. Importowanie najnowszej wersji: $1 ($2)" },
        { pattern: /Imported new version: (.+) \((.+)\)/, replacement: "Zaimportowano nową wersję: $1 ($2)" },
        { pattern: /Version sync failed: (.+)/, replacement: "Synchronizacja wersji nie powiodła się: $1" },
        { pattern: /Starting background check for (.+)/, replacement: "Rozpoczynanie sprawdzania w tle dla $1" },
        { pattern: /Checked (.+) against (.+) MC versions/, replacement: "Sprawdzono $1 pod kątem $2 wersji MC" },
        { pattern: /No target versions set\. Skipping check for new mod\./, replacement: "Nie ustawiono wersji docelowych. Pomijanie sprawdzania dla nowego moda." },
        { pattern: /Tracked mod '(.+)' not found for background check/, replacement: "Śledzony mod '$1' nie został znaleziony do sprawdzenia w tle" },
        { pattern: /Starting checks against (.+) MC version\+loader combinations/, replacement: "Rozpoczynanie sprawdzania dla $1 kombinacji wersji MC + loadera" },
        { pattern: /No tracked mods to check/, replacement: "Brak śledzonych modów do sprawdzenia" },
        { pattern: /Compatibility check completed/, replacement: "Sprawdzanie kompatybilności zakończone" },
        { pattern: /Background job failed: (.+)/, replacement: "Zadanie w tle nie powiodło się: $1" },
        { pattern: /Updated version (.+) \((.+)\) with official release time/, replacement: "Zaktualizowano wersję $1 ($2) o oficjalny czas wydania" },
        { pattern: /Could not find official details for (.+)\. Using defaults\./, replacement: "Nie można znaleźć oficjalnych szczegółów dla $1. Używanie domyślnych." },
        { pattern: /Starting compatibility checks for (.+) mods against (.+) \((.+)\)/, replacement: "Rozpoczynanie sprawdzania kompatybilności dla $1 modów z wersją $2 ($3)" },
        { pattern: /Completed checks for new version (.+) \((.+)\)/, replacement: "Zakończono sprawdzanie dla nowej wersji $1 ($2)" },
        { pattern: /Mod (.+) added for tracking \(channel: (.+)\)/, replacement: "Mod $1 dodany do śledzenia (kanał: $2)" },
        { pattern: /Mod (.+) removed from tracking \(including all versions and results\)/, replacement: "Mod $1 usunięty ze śledzenia (wraz ze wszystkimi wersjami i wynikami)" },
        { pattern: /Imported (.+) mods from YAML/, replacement: "Zaimportowano $1 modów z YAML" },
        { pattern: /Mod (.+) side updated to (.+)/, replacement: "Strona moda $1 zaktualizowana na $2" },
        { pattern: /Mod (.+) channel updated to (.+)/, replacement: "Kanał moda $1 zaktualizowany na $2" },
        { pattern: /Version (.+) \((.+)\) added/, replacement: "Wersja $1 ($2) dodana" },
        { pattern: /Version (.+) \((.+)\) added \(set as current\)/, replacement: "Wersja $1 ($2) dodana (ustawiona jako aktualna)" },
        { pattern: /Current version set to (.+) \((.+)\)/, replacement: "Aktualna wersja ustawiona na $1 ($2)" },
        { pattern: /Version (.+) \((.+)\) deleted/, replacement: "Wersja $1 ($2) usunięta" }
    ]
};
