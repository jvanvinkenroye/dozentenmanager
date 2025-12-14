# Theme System Documentation

## Übersicht

Das Dozentenmanager Theme-System bietet drei professionelle Farbschemata, zwischen denen Benutzer nahtlos wechseln können.

## Verfügbare Themes

### 1. Academic Blue (Standard) 🎓
- **ID:** `academic-blue`
- **Icon:** Graduation Cap
- **Beschreibung:** Professionell, vertrauenswürdig, zeitlos
- **Primärfarbe:** #2C5F8D (Dunkles Blau)
- **Akzent:** #FF6B35 (Warmes Orange)
- **WCAG:** AAA konform

### 2. Modern Mint 🌿
- **ID:** `modern-mint`
- **Icon:** Leaf
- **Beschreibung:** Frisch, modern, freundlich
- **Primärfarbe:** #008F7A (Teal/Türkis)
- **Akzent:** #845EC2 (Lila)
- **Fokus:** Moderne Ästhetik

### 3. University Navy 🏛️
- **ID:** `university-navy`
- **Icon:** University
- **Beschreibung:** Klassisch, elegant, autoritativ
- **Primärfarbe:** #003057 (Navy Blau)
- **Akzent:** #C1121F (Burgunderrot)
- **Fokus:** Traditionell akademisch

## Verwendung

### Theme-Wechsel

Benutzer können das Theme mit dem Button in der Navigationsleiste wechseln:
1. Klicken auf den "Theme"-Button (rechts oben)
2. Wechselt automatisch zum nächsten Theme
3. Einstellung wird in localStorage gespeichert
4. Kurze Benachrichtigung zeigt aktuelles Theme

### Programmatisches Wechseln

```javascript
// Theme direkt setzen
applyTheme('modern-mint');

// Zum nächsten Theme wechseln
cycleTheme();
```

## Technische Details

### CSS-Variablen

Alle Themes nutzen CSS Custom Properties (Variablen):

```css
--primary-color
--secondary-color
--accent-color
--success-color
--warning-color
--danger-color
--info-color
--bg-primary
--bg-secondary
--text-primary
--text-secondary
```

### Theme-Attribute

Themes werden über das `data-theme` Attribut am `<html>` Element gesteuert:

```html
<html data-theme="academic-blue">
<html data-theme="modern-mint">
<html data-theme="university-navy">
```

### Persistierung

Die Theme-Auswahl wird in localStorage gespeichert:

```javascript
localStorage.getItem('dozentenmanager-theme')
localStorage.setItem('dozentenmanager-theme', themeId)
```

## Neues Theme hinzufügen

1. **CSS-Variablen definieren** in `themes.css`:
   ```css
   [data-theme="new-theme-id"] {
       --primary-color: #HEXCODE;
       /* weitere Variablen */
   }
   ```

2. **Theme registrieren** in `theme-switcher.js`:
   ```javascript
   const themes = [
       /* existing themes */,
       { id: 'new-theme-id', name: 'New Theme Name', icon: 'fa-icon-name' }
   ];
   ```

3. **Barrierefreiheit prüfen:**
   - WCAG AA Mindestkontrast: 4.5:1 für Text
   - WCAG AAA bevorzugt: 7:1 für Text

## Barrierefreiheit

Alle Themes sind auf Barrierefreiheit getestet:

- ✅ Ausreichender Kontrast für Text
- ✅ Farbunabhängige Informationsvermittlung
- ✅ Keyboard-Navigation möglich
- ✅ Screen-Reader freundlich

## Browser-Kompatibilität

- ✅ Chrome/Edge 88+
- ✅ Firefox 78+
- ✅ Safari 14+
- ✅ Opera 74+

CSS Custom Properties werden von allen modernen Browsern unterstützt.

## Performance

- **CSS-Größe:** ~12 KB (unkomprimiert)
- **JS-Größe:** ~4 KB (unkomprimiert)
- **Transitions:** Smooth (300ms) für Theme-Wechsel
- **localStorage:** Minimal (< 50 Bytes)

## Anpassungen

### Eigene Farben überschreiben

```css
/* In custom.css */
:root {
    --primary-color: #YourColor !important;
}
```

### Transitions deaktivieren

```css
/* In custom.css */
* {
    transition: none !important;
}
```

## Wartung

### Theme-Konsistenz prüfen

Alle Themes sollten diese Elemente abdecken:
- Navigation (navbar)
- Buttons (all variants)
- Hero sections
- Cards
- Tables
- Forms
- Notifications
- Tags
- Footer

### Testing Checklist

- [ ] Alle Seiten in allen Themes anzeigen
- [ ] Kontrast-Verhältnisse prüfen
- [ ] Mobile Ansicht testen
- [ ] localStorage Persistierung prüfen
- [ ] Theme-Wechsel Performance
- [ ] Cross-Browser Testing

## Support

Bei Fragen oder Problemen:
- Dokumentation prüfen
- CSS-Variablen in DevTools inspizieren
- localStorage für Debugging leeren: `localStorage.removeItem('dozentenmanager-theme')`
