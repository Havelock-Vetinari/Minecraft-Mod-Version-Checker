if (typeof translations === 'undefined') var translations = {};

translations.en = {
    title: "Minecraft Mod Compatibility Checker",
    subtitle: "Check your mod compatibility with your Minecraft server version",
    current_mc_version: "Current MC Version",
    latest_official: "Latest Official",
    background_check_status: "Background Check Status",
    tracked_mods: "Tracked Mods",
    compatible_mods: "Compatible Mods",
    not_set: "Not Set",
    checking: "Checking...",
    last_check: "Last: {time}",
    next_check: "Next: {time}",
    never: "Never",
    tabs: {
        results: "Compatibility Results",
        add_mod: "Add Mod",
        versions: "Manage Versions",
        import_export: "Export/Import",
        logs: "Background Job Logs"
    },
    add_mod_panel: {
        title: "Add Mod to Track",
        slug_label: "Mod Slug (from Modrinth)",
        slug_placeholder: "e.g., sodium, lithium, iris",
        type_label: "Preferred Type",
        type_both: "Both (Client + Server)",
        type_client: "Client Only",
        type_server: "Server Only",
        channel_label: "Stability Channel",
        channel_stable: "Stable Releases Only",
        channel_beta: "Include Beta Versions",
        channel_alpha: "Include Alpha Versions",
        add_btn: "Add Mod",
        list_title: "Tracked Mods",
        empty: "No mods tracked yet"
    },
    manage_versions_panel: {
        title: "Manage Minecraft Versions",
        version_label: "Version (e.g., 1.21.1)",
        version_placeholder: "1.21.1",
        loader_label: "Loader",
        type_label: "Type",
        type_release: "Release",
        type_snapshot: "Snapshot",
        set_current_label: "Set as current server version",
        add_btn: "Add Version",
        list_title: "Version List",
        empty: "No versions added yet"
    },
    import_export_panel: {
        title: "Export / Import",
        description: "Manage your mod list using Docker Compose format (itzg/minecraft-server style).",
        export_version_label: "Select Minecraft Version for Export",
        no_compatible_versions: "No compatible versions found",
        export_hint: "Only versions where all server/both mods are compatible are shown (client-only mods are ignored).",
        yaml_label: "Compose YAML / MODRINTH_PROJECTS",
        yaml_placeholder: "Paste your docker-compose.yml here...",
        export_btn: "Export Current",
        import_btn: "Import from Above"
    },
    results_panel: {
        filter_version_label: "Filter by Minecraft Version",
        all_versions: "All Versions",
        filter_type_label: "Filter by Mod Type",
        all_types: "All Types",
        type_server: "Server Side (Server + Both)",
        type_client: "Client Side (Client + Both)",
        type_both: "Both Only",
        empty: "Add mods to see compatibility results",
        empty_filter: "No compatibility results found for selected filters."
    },
    logs_panel: {
        waiting: "Waiting for background job logs...",
        no_logs: "No logs yet. Background job will start soon..."
    },
    badges: {
        server: "Server",
        client: "Client",
        current: "Current"
    },
    mod_item: {
        supports: "Supports: {client} | {server}",
        no_client: "No Client",
        no_server: "No Server",
        remove_btn: "Remove"
    },
    version_item: {
        unknown_date: "Unknown date",
        set_current_btn: "Set Current",
        delete_btn: "Delete",
        delete_confirm: "Are you sure you want to delete this version? All associated compatibility results will be lost."
    },
    results_item: {
        mod_version: "Mod Version:",
        unknown: "Unknown"
    },
    status: {
        compatible: "Compatible",
        incompatible: "Incompatible",
        error: "Error"
    },
    toasts: {
        failed_load: "Failed to load initial data",
        enter_version: "Please enter a version",
        version_added: "Version added. Refreshing...",
        current_updated: "Current version updated",
        version_deleted: "Version deleted",
        enter_slug: "Please enter a mod slug",
        mod_added: "Mod added successfully",
        side_updated: "Mod side updated",
        channel_updated: "Mod channel updated",
        mod_removed: "Mod removed",
        failed_remove: "Failed to remove mod",
        select_export_version: "Please select a compatible version to export",
        exported_clipboard: "Exported and copied to clipboard!",
        exported_no_clipboard: "Exported! (Clipboard not supported in this browser/context)",
        exported_manual: "Exported! (Manual copy required)",
        paste_yaml: "Please paste YAML content first",
        import_success: "Successfully imported {count} new mods!"
    },
    log_patterns: [
        { pattern: /Database empty\. Importing latest version: (.+) \((.+)\)/, replacement: "Database empty. Importing latest version: $1 ($2)" },
        { pattern: /Imported new version: (.+) \((.+)\)/, replacement: "Imported new version: $1 ($2)" },
        { pattern: /Version sync failed: (.+)/, replacement: "Version sync failed: $1" },
        { pattern: /Starting background check for (.+)/, replacement: "Starting background check for $1" },
        { pattern: /Checked (.+) against (.+) MC versions/, replacement: "Checked $1 against $2 MC versions" },
        { pattern: /No target versions set\. Skipping check for new mod\./, replacement: "No target versions set. Skipping check for new mod." },
        { pattern: /Tracked mod '(.+)' not found for background check/, replacement: "Tracked mod '$1' not found for background check" },
        { pattern: /Starting checks against (.+) MC version\+loader combinations/, replacement: "Starting checks against $1 MC version+loader combinations" },
        { pattern: /No tracked mods to check/, replacement: "No tracked mods to check" },
        { pattern: /Compatibility check completed/, replacement: "Compatibility check completed" },
        { pattern: /Background job failed: (.+)/, replacement: "Background job failed: $1" },
        { pattern: /Updated version (.+) \((.+)\) with official release time/, replacement: "Updated version $1 ($2) with official release time" },
        { pattern: /Could not find official details for (.+)\. Using defaults\./, replacement: "Could not find official details for $1. Using defaults." },
        { pattern: /Starting compatibility checks for (.+) mods against (.+) \((.+)\)/, replacement: "Starting compatibility checks for $1 mods against $2 ($3)" },
        { pattern: /Completed checks for new version (.+) \((.+)\)/, replacement: "Completed checks for new version $1 ($2)" },
        { pattern: /Mod (.+) added for tracking \(channel: (.+)\)/, replacement: "Mod $1 added for tracking (channel: $2)" },
        { pattern: /Mod (.+) removed from tracking \(including all versions and results\)/, replacement: "Mod $1 removed from tracking (including all versions and results)" },
        { pattern: /Imported (.+) mods from YAML/, replacement: "Imported $1 mods from YAML" },
        { pattern: /Mod (.+) side updated to (.+)/, replacement: "Mod $1 side updated to $2" },
        { pattern: /Mod (.+) channel updated to (.+)/, replacement: "Mod $1 channel updated to $2" },
        { pattern: /Version (.+) \((.+)\) added/, replacement: "Version $1 ($2) added" },
        { pattern: /Version (.+) \((.+)\) added \(set as current\)/, replacement: "Version $1 ($2) added (set as current)" },
        { pattern: /Current version set to (.+) \((.+)\)/, replacement: "Current version set to $1 ($2)" },
        { pattern: /Version (.+) \((.+)\) deleted/, replacement: "Version $1 ($2) deleted" }
    ]
};
