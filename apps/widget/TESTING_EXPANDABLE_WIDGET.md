# Widget Expandable & Responsive - Testing Guide

## ✅ Implementation Complete

The expandable full-screen widget with responsive breakpoints has been successfully implemented!

### 📦 Files Created/Modified

#### New Files
1. **`apps/widget/src/hooks/useFullscreen.ts`** (60 lines)
   - Custom React hook for fullscreen state management
   - localStorage persistence (`agent_widget_expanded`)
   - ESC key listener (desktop/tablet only)
   - Window resize handler (auto-expand on mobile)
   - Returns: `isExpanded`, `toggleExpanded`, `collapse`, `expand`, `isMobile`

2. **`apps/widget/src/styles/responsive.css`** (280 lines)
   - Comprehensive responsive breakpoints
   - Mobile (<640px): Auto full-screen, no expand button
   - Tablet (640-1024px): Expandable widget
   - Desktop (>1024px): Expandable modal with backdrop
   - Smooth transitions (0.3s cubic-bezier)
   - Accessibility: focus-visible, high contrast, reduced motion
   - Dark mode support

3. **`apps/widget/test-responsive.html`** (200+ lines)
   - Comprehensive test suite interface
   - Device info display (viewport, user agent)
   - Test instructions for all breakpoints
   - Feature checklist
   - Keyboard shortcuts reference

#### Modified Files
1. **`apps/widget/src/stores/widgetStore.ts`**
   - Added `isExpanded: boolean` state
   - Added `setExpanded()` and `toggleExpanded()` actions

2. **`apps/widget/src/App.tsx`**
   - Imported `useFullscreen` hook and `responsive.css`
   - Integrated fullscreen state with store
   - Added dynamic `expanded` className to widget-overlay
   - Passed `isExpanded`, `isMobile`, `onToggleExpand` props to ChatWindow

3. **`apps/widget/src/components/ChatWindow.tsx`**
   - Updated `ChatWindowProps` with optional props: `isExpanded?`, `isMobile?`, `onToggleExpand?`
   - Added dynamic classNames: `chat-window ${isExpanded ? 'expanded' : ''} ${isMobile ? 'mobile' : ''}`
   - Added header-actions wrapper with expand/collapse button
   - Conditional rendering: expand button only on desktop/tablet (!isMobile)
   - SVG icons for expand/collapse states
   - Accessibility: aria-label, title attributes

4. **`apps/widget/src/App.css`**
   - Removed conflicting widget-overlay positioning
   - Removed old responsive breakpoint
   - Removed header button styles (moved to responsive.css)

---

## 🧪 Testing Instructions

### 🚀 Quick Start

```bash
# From apps/widget directory
cd apps/widget

# Start development server
npm run dev

# Open test page (should auto-open at http://localhost:5173)
# Or manually navigate to: http://localhost:5173/test-responsive.html
```

### 📱 Device Testing Scenarios

#### 1. **Mobile Testing (<640px)**
**Expected Behavior:**
- ✅ Widget button visible in bottom-right
- ✅ Click widget → Opens full-screen (100vw × 100vh)
- ✅ No border-radius (flat edges)
- ✅ No expand button visible (auto full-screen)
- ✅ Only close button (×) in header
- ✅ Input has safe area for keyboard
- ✅ Touch-friendly buttons (min 44×44px)
- ✅ Smooth iOS scrolling (-webkit-overflow-scrolling: touch)

**Test Steps:**
1. Resize browser to <640px width OR use Chrome DevTools mobile emulation
2. Click widget button
3. Verify full-screen layout
4. Verify no expand button in header
5. Type message → check keyboard doesn't cover input
6. Try to scroll messages → should be smooth

**DevTools Emulation:**
- iPhone SE (375×667)
- iPhone 12 Pro (390×844)
- Pixel 5 (393×851)

#### 2. **Tablet Testing (640-1024px)**
**Expected Behavior:**
- ✅ Widget starts as 420px × 600px window
- ✅ Positioned bottom-right with 20px margin
- ✅ Expand button visible in header
- ✅ Click expand → Widget fills viewport minus 40px margin
- ✅ ESC key collapses widget
- ✅ Border-radius: 12px maintained
- ✅ Preference saved in localStorage

**Test Steps:**
1. Resize browser to 768px width
2. Click widget button → should open as floating window
3. Click expand button (squares icon) → should expand
4. Press ESC key → should collapse
5. Close and reopen widget → should remember expanded state
6. Reload page, open widget → should restore saved state

**DevTools Emulation:**
- iPad Mini (768×1024)
- iPad Air (820×1180)
- Surface Pro 7 (912×1368)

#### 3. **Desktop Testing (>1024px)**
**Expected Behavior:**
- ✅ Widget starts as 400px × 600px window
- ✅ Positioned bottom-right with 20px margin
- ✅ Expand button visible
- ✅ Click expand → Widget becomes 90vw × 90vh modal (max 1400px)
- ✅ Centered in viewport
- ✅ Backdrop overlay visible
- ✅ ESC key collapses
- ✅ Border-radius: 16px when expanded

**Test Steps:**
1. Use full desktop browser (>1024px width)
2. Click widget button
3. Click expand button
4. Verify centered modal appearance
5. Verify backdrop overlay behind widget
6. Press ESC → should collapse
7. Verify max-width cap at 1400px (on very wide screens)

**Screen Sizes:**
- 1366×768 (HD Laptop)
- 1920×1080 (Full HD Desktop)
- 2560×1440 (2K Desktop)

---

## ⌨️ Keyboard Testing

### ESC Key Behavior
**Expected:**
- ✅ Desktop/Tablet: ESC collapses expanded widget
- ✅ Mobile: ESC does nothing (mobile auto full-screen)
- ✅ Widget closed: ESC does nothing
- ✅ Widget open but not expanded: ESC does nothing

**Test Steps:**
1. Open widget on desktop → Press ESC → nothing happens
2. Expand widget → Press ESC → should collapse
3. Collapse manually with button → Press ESC → nothing happens
4. On mobile → ESC never affects widget

### Tab Navigation
**Expected:**
- ✅ Tab cycles through: expand button → close button → input → send button
- ✅ Focus visible outlines (blue ring)
- ✅ No keyboard traps

**Test Steps:**
1. Open widget
2. Press Tab repeatedly
3. Verify focus moves through all interactive elements
4. Verify visible focus indicators

---

## 💾 localStorage Testing

### Persistence Behavior
**Key:** `agent_widget_expanded`
**Values:** `"true"` or `"false"`

**Expected:**
- ✅ Mobile: localStorage not used (always full-screen)
- ✅ Desktop/Tablet: State saved on expand/collapse
- ✅ Preference persists across page reloads
- ✅ Preference persists across tab closes

**Test Steps:**
1. Open widget on desktop
2. Expand widget → check localStorage in DevTools
   ```javascript
   localStorage.getItem('agent_widget_expanded') // should be "true"
   ```
3. Collapse widget → check localStorage
   ```javascript
   localStorage.getItem('agent_widget_expanded') // should be "false"
   ```
4. Reload page → open widget → should restore last state
5. Close browser → reopen → open widget → should restore state

**DevTools:**
```javascript
// View current state
console.log(localStorage.getItem('agent_widget_expanded'));

// Clear preference (reset)
localStorage.removeItem('agent_widget_expanded');

// Set preference manually
localStorage.setItem('agent_widget_expanded', 'true');
```

---

## 🎨 Visual Testing

### Animations
**Expected:**
- ✅ Expand: smooth transition over 0.3s
- ✅ Collapse: smooth transition over 0.3s
- ✅ Backdrop: fade-in animation
- ✅ No janky movements or layout shifts

**Test Steps:**
1. Expand/collapse several times
2. Watch for smooth transitions
3. Check for any flickering or jumping
4. Verify backdrop appears/disappears smoothly

### Button States
**Expected:**
- ✅ Expand button: hover shows gray background
- ✅ Expand button: active shows darker background
- ✅ Close button: hover shows gray background
- ✅ Icons: collapse icon when expanded, expand icon when collapsed

**Test Steps:**
1. Hover over expand button → should show gray background
2. Click and hold → should show darker background
3. Release → should return to normal
4. Verify icon changes: 4 arrows out (expand) vs 4 arrows in (collapse)

---

## ♿ Accessibility Testing

### Focus Management
**Expected:**
- ✅ Focus visible: 2px blue outline with 2px offset
- ✅ Focus order: logical (expand → close → input → send)
- ✅ No focus traps

**Test Steps:**
1. Navigate with Tab key only
2. Verify all interactive elements are reachable
3. Verify focus order makes sense
4. Verify clear focus indicators

### ARIA Attributes
**Expected:**
- ✅ Expand button: `aria-label="Expand"` or `aria-label="Collapse"`
- ✅ Expand button: `title="Expand"` or `title="Collapse (ESC)"`

**Test Steps:**
1. Inspect expand button in DevTools
2. Verify aria-label changes based on state
3. Hover over button → verify tooltip matches state

### High Contrast Mode
**Expected:**
- ✅ Widget has visible border
- ✅ Buttons have visible borders
- ✅ All text is readable

**Test Steps:**
1. Enable high contrast mode (Windows: Alt+Shift+PrtScn)
2. Verify all UI elements are visible
3. Verify sufficient contrast

### Reduced Motion
**Expected:**
- ✅ Animations disabled
- ✅ Transitions removed
- ✅ Instant state changes

**Test Steps:**
1. Enable reduced motion (macOS: System Preferences → Accessibility → Display → Reduce Motion)
2. Expand/collapse widget
3. Verify instant state changes (no animation)

---

## 🌙 Dark Mode Testing

**Expected:**
- ✅ Widget background: `#1f2937` (dark gray)
- ✅ Text color: `#f9fafb` (light)
- ✅ Header background: `#111827` (darker gray)
- ✅ Buttons: proper contrast in dark mode

**Test Steps:**
1. Enable dark mode (macOS: System Preferences → General → Appearance → Dark)
2. Open widget
3. Verify dark theme applied
4. Verify text is readable
5. Verify buttons have proper contrast

**DevTools:**
```javascript
// Force dark mode in DevTools
// Chrome: DevTools → ... → More tools → Rendering → Emulate CSS media feature prefers-color-scheme
```

---

## 🐛 Bug Testing

### Edge Cases
**Test these scenarios:**

1. **Rapid expand/collapse**
   - Click expand button 10 times quickly
   - Should handle gracefully without errors

2. **ESC spam**
   - Press ESC repeatedly when expanded
   - Should only collapse once, no errors

3. **Window resize during expansion**
   - Expand widget on desktop
   - Resize window to mobile size
   - Should adapt gracefully

4. **localStorage disabled**
   - Disable localStorage in browser
   - Widget should still work (just won't save preference)

5. **Very small viewport**
   - Test at 320×568 (iPhone SE 1st gen)
   - Should still be usable

6. **Very large viewport**
   - Test at 2560×1440 or wider
   - Expanded widget should cap at 1400px width

---

## 📊 Performance Testing

### Metrics to Check
**Expected:**
- ✅ Expand/collapse animation: 60 FPS
- ✅ No layout thrashing
- ✅ CSS transitions (not JS animations)

**DevTools Testing:**
1. Open Chrome DevTools → Performance tab
2. Start recording
3. Expand/collapse widget several times
4. Stop recording
5. Check for:
   - Smooth 60 FPS
   - No long tasks
   - Minimal layout recalculations

---

## ✅ Acceptance Checklist

### Functional Requirements
- [ ] Widget opens as floating window on desktop/tablet
- [ ] Widget opens full-screen on mobile
- [ ] Expand button visible on desktop/tablet
- [ ] Expand button hidden on mobile
- [ ] Click expand → widget expands
- [ ] Click collapse → widget collapses
- [ ] ESC key collapses (desktop/tablet only)
- [ ] Close button (×) closes widget
- [ ] localStorage saves preference
- [ ] Preference persists across reloads

### Visual Requirements
- [ ] Smooth transitions (0.3s)
- [ ] No janky animations
- [ ] Backdrop appears when expanded (desktop)
- [ ] Icons change based on state
- [ ] Hover states work
- [ ] Focus states visible

### Responsive Requirements
- [ ] Mobile: 100vw × 100vh, no border-radius
- [ ] Tablet: 420×600 → full viewport - 40px
- [ ] Desktop: 400×600 → 90vw×90vh (max 1400px)
- [ ] Message bubbles responsive width
- [ ] Touch-friendly buttons on mobile
- [ ] Safe area for keyboard on mobile

### Accessibility Requirements
- [ ] Focus visible outlines
- [ ] Keyboard navigation works
- [ ] ARIA labels present
- [ ] High contrast mode supported
- [ ] Reduced motion supported
- [ ] No focus traps

### Browser Compatibility
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari (macOS/iOS)
- [ ] Mobile browsers (Chrome Android, Safari iOS)

---

## 🔧 Debugging Tools

### Browser Console Commands
```javascript
// Check current state
const store = window.__WIDGET_STORE__;
console.log('Is expanded:', store.getState().isExpanded);

// Check localStorage
console.log('Saved preference:', localStorage.getItem('agent_widget_expanded'));

// Clear preference
localStorage.removeItem('agent_widget_expanded');

// Force expand
store.getState().setExpanded(true);

// Force collapse
store.getState().setExpanded(false);

// Check device type
console.log('Is mobile:', window.innerWidth < 640);
console.log('Is tablet:', window.innerWidth >= 640 && window.innerWidth < 1024);
console.log('Is desktop:', window.innerWidth >= 1024);
```

### DevTools Breakpoints
Set breakpoints in:
1. `useFullscreen.ts` → `toggleExpanded` function
2. `ChatWindow.tsx` → `onToggleExpand` callback
3. `App.tsx` → `useEffect` sync logic

---

## 📝 Known Issues / Future Enhancements

### Potential Issues
- **Safari iOS**: May need `-webkit-overflow-scrolling: touch` for smooth scrolling ✅ (already added)
- **Older browsers**: `env(safe-area-inset-bottom)` may not work (graceful fallback to 0px) ✅ (already handled)

### Future Enhancements
- [ ] Add transition speed setting (slow/normal/fast)
- [ ] Add option to disable animations
- [ ] Add custom breakpoint configuration
- [ ] Add portrait/landscape detection
- [ ] Add minimize button (collapse to header bar)
- [ ] Add window dragging on desktop

---

## 🎯 Success Criteria

The feature is considered **successfully implemented** if:

1. ✅ All functional requirements met
2. ✅ All responsive breakpoints working
3. ✅ Accessibility requirements met
4. ✅ No console errors
5. ✅ Smooth performance (60 FPS)
6. ✅ localStorage persistence working
7. ✅ Works across major browsers

---

## 📚 Related Documentation

- **ROADMAP.md**: Full specification for this feature
- **apps/widget/README.md**: Widget setup and configuration
- **apps/widget/AGENTS.md**: Widget-specific agent guidelines

---

## 🚀 Next Steps

After testing is complete:

1. **Fix any bugs found** during testing
2. **Optimize performance** if needed
3. **Update documentation** with any changes
4. **Commit changes** to git
5. **Move to next roadmap item**: BM25 Threshold Optimization

---

**Happy Testing! 🎉**
