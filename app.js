// Minecraft Mod Version Checker Application

// Mock database of popular mods with their version compatibility
const modsDatabase = {
    'jei': {
        name: 'Just Enough Items (JEI)',
        versions: {
            '1.20.4': ['forge', 'fabric', 'neoforge'],
            '1.20.3': ['forge', 'fabric', 'neoforge'],
            '1.20.2': ['forge', 'fabric', 'neoforge'],
            '1.20.1': ['forge', 'fabric', 'neoforge'],
            '1.20': ['forge', 'fabric'],
            '1.19.4': ['forge', 'fabric'],
            '1.19.3': ['forge', 'fabric'],
            '1.19.2': ['forge', 'fabric'],
            '1.19.1': ['forge', 'fabric'],
            '1.19': ['forge', 'fabric'],
            '1.18.2': ['forge', 'fabric'],
            '1.18.1': ['forge', 'fabric'],
            '1.18': ['forge', 'fabric'],
            '1.16.5': ['forge'],
            '1.12.2': ['forge']
        }
    },
    'optifine': {
        name: 'OptiFine',
        versions: {
            '1.20.4': ['forge'],
            '1.20.2': ['forge'],
            '1.20.1': ['forge'],
            '1.19.4': ['forge'],
            '1.19.3': ['forge'],
            '1.19.2': ['forge'],
            '1.18.2': ['forge'],
            '1.18.1': ['forge'],
            '1.17.1': ['forge'],
            '1.16.5': ['forge'],
            '1.12.2': ['forge']
        }
    },
    'sodium': {
        name: 'Sodium',
        versions: {
            '1.20.4': ['fabric'],
            '1.20.3': ['fabric'],
            '1.20.2': ['fabric'],
            '1.20.1': ['fabric'],
            '1.20': ['fabric'],
            '1.19.4': ['fabric'],
            '1.19.3': ['fabric'],
            '1.19.2': ['fabric'],
            '1.19.1': ['fabric'],
            '1.19': ['fabric'],
            '1.18.2': ['fabric'],
            '1.18.1': ['fabric'],
            '1.17.1': ['fabric'],
            '1.16.5': ['fabric']
        }
    },
    'iris': {
        name: 'Iris Shaders',
        versions: {
            '1.20.4': ['fabric'],
            '1.20.2': ['fabric'],
            '1.20.1': ['fabric'],
            '1.19.4': ['fabric'],
            '1.19.3': ['fabric'],
            '1.19.2': ['fabric'],
            '1.18.2': ['fabric'],
            '1.18.1': ['fabric'],
            '1.17.1': ['fabric']
        }
    },
    'biomes o plenty': {
        name: 'Biomes O\' Plenty',
        versions: {
            '1.20.4': ['forge', 'neoforge'],
            '1.20.2': ['forge', 'neoforge'],
            '1.20.1': ['forge', 'fabric'],
            '1.19.4': ['forge', 'fabric'],
            '1.19.3': ['forge', 'fabric'],
            '1.19.2': ['forge', 'fabric'],
            '1.18.2': ['forge', 'fabric'],
            '1.16.5': ['forge'],
            '1.12.2': ['forge']
        }
    },
    'twilight forest': {
        name: 'The Twilight Forest',
        versions: {
            '1.20.4': ['forge', 'neoforge'],
            '1.20.1': ['forge'],
            '1.19.4': ['forge'],
            '1.19.2': ['forge'],
            '1.18.2': ['forge'],
            '1.16.5': ['forge'],
            '1.12.2': ['forge']
        }
    },
    'applied energistics': {
        name: 'Applied Energistics 2',
        versions: {
            '1.20.4': ['forge', 'fabric', 'neoforge'],
            '1.20.1': ['forge', 'fabric'],
            '1.19.2': ['forge', 'fabric'],
            '1.18.2': ['forge', 'fabric'],
            '1.16.5': ['forge'],
            '1.12.2': ['forge']
        }
    },
    'create': {
        name: 'Create',
        versions: {
            '1.20.4': ['forge', 'fabric', 'neoforge'],
            '1.20.1': ['forge', 'fabric'],
            '1.19.2': ['forge', 'fabric'],
            '1.18.2': ['forge', 'fabric'],
            '1.16.5': ['forge']
        }
    },
    'thermal expansion': {
        name: 'Thermal Expansion',
        versions: {
            '1.19.2': ['forge'],
            '1.18.2': ['forge'],
            '1.16.5': ['forge'],
            '1.12.2': ['forge']
        }
    },
    'tinkers construct': {
        name: 'Tinkers\' Construct',
        versions: {
            '1.19.2': ['forge'],
            '1.18.2': ['forge'],
            '1.16.5': ['forge'],
            '1.12.2': ['forge']
        }
    },
    'journeymap': {
        name: 'JourneyMap',
        versions: {
            '1.20.4': ['forge', 'fabric', 'neoforge'],
            '1.20.2': ['forge', 'fabric'],
            '1.20.1': ['forge', 'fabric'],
            '1.19.4': ['forge', 'fabric'],
            '1.19.2': ['forge', 'fabric'],
            '1.18.2': ['forge', 'fabric'],
            '1.16.5': ['forge'],
            '1.12.2': ['forge']
        }
    },
    'waystones': {
        name: 'Waystones',
        versions: {
            '1.20.4': ['forge', 'fabric', 'neoforge'],
            '1.20.1': ['forge', 'fabric'],
            '1.19.4': ['forge', 'fabric'],
            '1.19.2': ['forge', 'fabric'],
            '1.18.2': ['forge', 'fabric'],
            '1.16.5': ['forge'],
            '1.12.2': ['forge']
        }
    }
};

// State management
let addedMods = [];

// DOM elements
const minecraftVersionSelect = document.getElementById('minecraft-version');
const modLoaderSelect = document.getElementById('mod-loader');
const modNameInput = document.getElementById('mod-name');
const checkButton = document.getElementById('check-button');
const addModButton = document.getElementById('add-mod-button');
const modsListSection = document.getElementById('mods-list-section');
const modsList = document.getElementById('mods-list');
const checkAllButton = document.getElementById('check-all-button');
const clearListButton = document.getElementById('clear-list-button');
const resultsSection = document.getElementById('results-section');
const resultsContainer = document.getElementById('results-container');

// Event listeners
checkButton.addEventListener('click', checkSingleMod);
addModButton.addEventListener('click', addModToList);
checkAllButton.addEventListener('click', checkAllMods);
clearListButton.addEventListener('click', clearModsList);
modNameInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        checkSingleMod();
    }
});

// Functions
function normalizeModName(name) {
    return name.toLowerCase().trim();
}

function findMod(modName) {
    const normalized = normalizeModName(modName);
    
    // Direct match
    if (modsDatabase[normalized]) {
        return modsDatabase[normalized];
    }
    
    // Partial match
    for (const [key, mod] of Object.entries(modsDatabase)) {
        if (key.includes(normalized) || normalized.includes(key)) {
            return mod;
        }
        if (mod.name.toLowerCase().includes(normalized)) {
            return mod;
        }
    }
    
    return null;
}

function checkCompatibility(modName, minecraftVersion, modLoader) {
    const mod = findMod(modName);
    
    if (!mod) {
        return {
            found: false,
            modName: modName,
            message: 'Mod not found in database'
        };
    }
    
    const versionSupport = mod.versions[minecraftVersion];
    
    if (!versionSupport) {
        return {
            found: true,
            modName: mod.name,
            compatible: false,
            status: 'incompatible',
            message: `${mod.name} does not support Minecraft ${minecraftVersion}`,
            availableVersions: Object.keys(mod.versions)
        };
    }
    
    if (!versionSupport.includes(modLoader.toLowerCase())) {
        return {
            found: true,
            modName: mod.name,
            compatible: false,
            status: 'incompatible',
            message: `${mod.name} supports Minecraft ${minecraftVersion} but not with ${modLoader}`,
            supportedLoaders: versionSupport
        };
    }
    
    return {
        found: true,
        modName: mod.name,
        compatible: true,
        status: 'compatible',
        message: `${mod.name} is fully compatible with Minecraft ${minecraftVersion} using ${modLoader}!`
    };
}

function validateInputs() {
    const version = minecraftVersionSelect.value;
    const loader = modLoaderSelect.value;
    const modName = modNameInput.value.trim();
    
    if (!version) {
        alert('Please select a Minecraft version');
        return null;
    }
    
    if (!loader) {
        alert('Please select a mod loader');
        return null;
    }
    
    if (!modName) {
        alert('Please enter a mod name');
        return null;
    }
    
    return { version, loader, modName };
}

function checkSingleMod() {
    const inputs = validateInputs();
    if (!inputs) return;
    
    const result = checkCompatibility(inputs.modName, inputs.version, inputs.loader);
    displayResults([result]);
}

function addModToList() {
    const inputs = validateInputs();
    if (!inputs) return;
    
    // Check if mod already in list
    const exists = addedMods.some(mod => 
        normalizeModName(mod.modName) === normalizeModName(inputs.modName)
    );
    
    if (exists) {
        alert('This mod is already in your list');
        return;
    }
    
    addedMods.push({
        modName: inputs.modName,
        version: inputs.version,
        loader: inputs.loader
    });
    
    updateModsList();
    modNameInput.value = '';
    modNameInput.focus();
}

function updateModsList() {
    if (addedMods.length === 0) {
        modsListSection.style.display = 'none';
        return;
    }
    
    modsListSection.style.display = 'block';
    modsList.innerHTML = '';
    
    addedMods.forEach((mod, index) => {
        const modItem = document.createElement('div');
        modItem.className = 'mod-item';
        modItem.innerHTML = `
            <div class="mod-info">
                <div class="mod-name">${mod.modName}</div>
                <div class="mod-details">Minecraft ${mod.version} • ${mod.loader}</div>
            </div>
            <button class="remove-btn" onclick="removeMod(${index})">Remove</button>
        `;
        modsList.appendChild(modItem);
    });
}

function removeMod(index) {
    addedMods.splice(index, 1);
    updateModsList();
}

function checkAllMods() {
    if (addedMods.length === 0) {
        alert('Please add mods to the list first');
        return;
    }
    
    const results = addedMods.map(mod => 
        checkCompatibility(mod.modName, mod.version, mod.loader)
    );
    
    displayResults(results);
}

function clearModsList() {
    if (confirm('Are you sure you want to clear the list?')) {
        addedMods = [];
        updateModsList();
        resultsSection.style.display = 'none';
    }
}

function displayResults(results) {
    resultsSection.style.display = 'block';
    resultsContainer.innerHTML = '';
    
    results.forEach(result => {
        const card = document.createElement('div');
        
        if (!result.found) {
            card.className = 'result-card warning';
            card.innerHTML = `
                <div class="result-header">
                    <div class="result-mod-name">${result.modName}</div>
                    <span class="status-badge warning">Not Found</span>
                </div>
                <div class="result-details">
                    <p>${result.message}</p>
                    <p><strong>Tip:</strong> Try searching with a different name or check the mod's official page.</p>
                    <p>The mod might be available but not in our database yet.</p>
                </div>
            `;
        } else if (result.compatible) {
            card.className = 'result-card compatible';
            card.innerHTML = `
                <div class="result-header">
                    <div class="result-mod-name">${result.modName}</div>
                    <span class="status-badge compatible">✓ Compatible</span>
                </div>
                <div class="result-details">
                    <p>✅ ${result.message}</p>
                    <p><strong>Status:</strong> This mod should work perfectly with your setup!</p>
                </div>
            `;
        } else {
            card.className = 'result-card incompatible';
            let additionalInfo = '';
            
            if (result.availableVersions) {
                additionalInfo = `<p><strong>Available for:</strong> ${result.availableVersions.join(', ')}</p>`;
            }
            
            if (result.supportedLoaders) {
                additionalInfo += `<p><strong>Supported loaders for this version:</strong> ${result.supportedLoaders.join(', ')}</p>`;
            }
            
            card.innerHTML = `
                <div class="result-header">
                    <div class="result-mod-name">${result.modName}</div>
                    <span class="status-badge incompatible">✗ Incompatible</span>
                </div>
                <div class="result-details">
                    <p>❌ ${result.message}</p>
                    ${additionalInfo}
                    <p><strong>Suggestion:</strong> Try a different Minecraft version or mod loader that this mod supports.</p>
                </div>
            `;
        }
        
        resultsContainer.appendChild(card);
    });
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Initialize
console.log('Minecraft Mod Version Checker loaded');
console.log(`Database contains ${Object.keys(modsDatabase).length} mods`);
