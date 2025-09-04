# E-ink Display Optimization Tasks

## **Issues Found During Pi Testing**

### **Team Logo Issues:**

### **Color Optimization Notes:**

- Current gray optimizations (#333/#444) may still be too light for 6-color e-ink dithering
- Consider going even darker or switching to pure black for secondary elements
- Yellow team logos are problematic - might need white versions or different approach
- E-ink displays work best with high contrast (black/white) rather than mid-tones

### **Testing Status:**

- ✅ **Test data setup** - Using `?test=true` for comprehensive 16-game layout
- ✅ **6-color dithering** - Implemented with proper Inky palette
- ✅ **Typography enhanced** - Larger fonts and better weights
- ✅ **E-ink legibility mode** - Transparent backgrounds, black text

### **Priority Order:**

1. **Borders** - Quick CSS fixes for visibility
2. **Typography** - Font weight adjustments
3. **Diamond elements** - Color and asset updates
4. **Team logos** - Asset replacements for problematic yellows

### **After Pi Testing:**

- [ ] **Remove test data flag** - Change config back to live data
- [ ] **Document final optimizations** - Update README with e-ink specific features
