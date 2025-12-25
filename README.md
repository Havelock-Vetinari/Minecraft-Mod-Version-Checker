# Minecraft Mod Version Checker 🎮

A web application for checking Minecraft mods version compatibility. This tool helps Minecraft players verify if their favorite mods are compatible with their Minecraft version and mod loader.

## Features

- ✅ **Version Compatibility Checking** - Verify if mods work with specific Minecraft versions
- 🔧 **Mod Loader Support** - Check compatibility for Forge, Fabric, Quilt, and NeoForge
- 📝 **Batch Checking** - Add multiple mods and check them all at once
- 🎨 **User-Friendly Interface** - Clean, modern design with intuitive controls
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile devices

## Supported Mods

The database includes popular mods such as:
- Just Enough Items (JEI)
- OptiFine
- Sodium
- Iris Shaders
- Biomes O' Plenty
- The Twilight Forest
- Applied Energistics 2
- Create
- Thermal Expansion
- Tinkers' Construct
- JourneyMap
- Waystones
- And more!

## How to Use

### Online Usage

1. Open `index.html` in your web browser
2. Select your Minecraft version from the dropdown
3. Choose your mod loader (Forge, Fabric, Quilt, or NeoForge)
4. Enter a mod name to check
5. Click "Check Compatibility" for instant results

### Running Locally

#### Option 1: Simple Web Server (Recommended)

```bash
# Using Python 3
python3 -m http.server 8000

# Or using npm
npm start
```

Then open your browser to `http://localhost:8000`

#### Option 2: Direct File Access

Simply open `index.html` directly in your web browser by double-clicking the file.

## Installation

1. Clone this repository:
```bash
git clone https://github.com/Havelock-Vetinari/Minecraft-Mod-Version-Checker.git
cd Minecraft-Mod-Version-Checker
```

2. Open `index.html` in your web browser or run a local server:
```bash
python3 -m http.server 8000
```

## Project Structure

```
Minecraft-Mod-Version-Checker/
├── index.html          # Main HTML file with the UI structure
├── styles.css          # CSS styling for the application
├── app.js             # JavaScript with mod compatibility logic
├── package.json       # Project metadata and scripts
├── README.md          # This file
└── .gitignore        # Git ignore configuration
```

## Technologies Used

- **HTML5** - Semantic markup structure
- **CSS3** - Modern styling with gradients and animations
- **JavaScript (ES6+)** - Interactive functionality and compatibility checking
- **No external dependencies** - Pure vanilla JavaScript for maximum compatibility

## Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge
- Opera

## Contributing

Contributions are welcome! To add more mods to the database:

1. Fork the repository
2. Edit `app.js` and add mod entries to the `modsDatabase` object
3. Follow the existing format for mod entries
4. Submit a pull request

### Mod Entry Format

```javascript
'mod-name': {
    name: 'Full Mod Name',
    versions: {
        '1.20.4': ['forge', 'fabric', 'neoforge'],
        '1.19.2': ['forge', 'fabric'],
        // Add more versions as needed
    }
}
```

## Future Enhancements

- [ ] Integration with CurseForge API
- [ ] Integration with Modrinth API
- [ ] Mod dependency checking
- [ ] Save/load mod lists
- [ ] Export compatibility reports
- [ ] Dark mode toggle
- [ ] Mod search with autocomplete

## License

MIT License - Feel free to use this project for any purpose.

## Acknowledgments

- Built for the Minecraft modding community
- Inspired by the need for easy mod compatibility checking
- Special thanks to all mod developers who make Minecraft amazing

## Disclaimer

This tool provides compatibility information based on mod metadata and version patterns. Always verify with the mod's official page (CurseForge, Modrinth, etc.) for the most accurate and up-to-date information.

---

Made with ❤️ for Minecraft players and modders worldwide