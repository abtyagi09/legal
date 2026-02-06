# Settings Panel Guide

## ✅ Deployment Complete
**New Revision**: ca-7alsezpsk27uq--20260205164825  
**Agent URL**: https://ca-7alsezpsk27uq.wittymoss-05f49619.eastus2.azurecontainerapps.io

## 🎯 What's New

A comprehensive settings panel has been added that slides in from the right side of the screen with a beautiful interface.

## ⚙️ Settings Panel Features

### How to Access
- Click the **⚙️ settings icon** in the top-right corner (fixed position, floats over content)
- Panel slides in from the right with smooth animation
- Click outside the panel or the X button to close it

### Available Settings

#### 1. 🔒 Document-Level Security
- **Toggle**: Enable/Disable document security filtering
- **When Enabled**: You only see documents you uploaded
- **When Disabled**: You see all documents in the system (if you have access)
- **Default**: Enabled
- **Affects**: Document list and search results

#### 2. 🤖 Enable Integration Actions
- **Toggle**: Enable/Disable function calling and integration features
- **When Enabled**: Agent can:
  - Call external APIs (mock legal API)
  - Send email notifications
  - Send Teams notifications
  - Generate invoices
  - Create and manage legal cases
  - Search attorneys
  - Get legal rates
  - Calculate cost estimates
- **When Disabled**: Agent works in basic chat mode (RAG only)
- **Default**: Enabled
- **Affects**: Agent capabilities and available features

### Settings Persistence
- ✅ All settings are saved to **browser localStorage**
- ✅ Settings persist across browser sessions
- ✅ Settings are synchronized between the settings panel and legacy toggles
- ✅ Visual confirmation when settings are saved (2-second notification)

## 🎨 UI/UX Features

### Design Elements
- **Floating Button**: Fixed position settings icon with hover effects
- **Slide-in Animation**: Smooth 300ms transition from right
- **Overlay**: Semi-transparent backdrop when panel is open
- **Responsive**: 400px wide panel, full height
- **Gradient Header**: Purple gradient matching app theme
- **Clear Sections**: Organized by Security, Agent Features, and About
- **Descriptive Labels**: Each setting has a title and detailed description
- **Status Notifications**: Visual feedback when settings are saved
- **Accessibility**: Proper labels, hover states, and keyboard support

### Interaction
1. **Open**: Click ⚙️ button or settings option
2. **Configure**: Toggle switches as needed
3. **Auto-save**: Settings save immediately on change
4. **Feedback**: "✓ Settings saved" notification appears
5. **Close**: Click X, overlay, or press Escape

## 🔧 Technical Implementation

### Frontend (JavaScript)
```javascript
// Get settings from localStorage
getSecurityEnabled()  // Returns true/false
getFunctionsEnabled() // Returns true/false

// Update settings
updateSecuritySetting()  // Saves and reloads documents
updateFunctionsSetting() // Saves to localStorage

// Panel control
toggleSettingsPanel()    // Opens/closes the panel
loadSettingsState()      // Loads settings on page load
```

### Backend (API)
```python
# ChatMessage model includes:
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    security_enabled: Optional[bool] = True
    enable_functions: Optional[bool] = True  # New!

# Agent chat method receives:
async def chat(
    message, 
    session_id, 
    user_id,
    security_enabled,     # From settings
    enable_functions      # From settings
)
```

### CSS Styling
- `.settings-btn` - Floating button (fixed position, z-index 1000)
- `.settings-panel` - Side panel (400px, slides from right)
- `.settings-overlay` - Background overlay (rgba fade)
- `.settings-section` - Organized sections with borders
- `.settings-item` - Individual setting with label/description
- `.settings-status` - Save confirmation notification

## 📝 Usage Examples

### Test Integration Actions

1. **Open Settings** (click ⚙️)
2. **Ensure "Enable Integration Actions" is ON**
3. **Try these commands**:

```
Create a new case with title 'Smith v. Jones', type 'Contract Dispute', 
client 'John Smith', and attorney_id 'att-001'
```

```
Get all available attorneys and show me their specialties and rates
```

```
Calculate the cost for 10 hours of Contract Review work and generate 
an invoice for John Smith (john@example.com)
```

### Test Security Filtering

1. **Open Settings**
2. **Toggle "Document-Level Security" OFF**
3. **Check document list** - should see all documents
4. **Toggle it back ON**
5. **Check document list** - should only see your documents

### Test Basic Mode (No Functions)

1. **Open Settings**
2. **Turn OFF "Enable Integration Actions"**
3. **Chat with agent** - should only use RAG (document search)
4. **Try asking for external API data** - agent won't make API calls
5. **Turn it back ON** - agent can use all features again

## 🚀 Benefits

### User Control
- ✅ Users can toggle features based on their needs
- ✅ Privacy-conscious users can enable strict security
- ✅ Power users can enable all features
- ✅ Easy to troubleshoot by disabling features

### Developer Benefits
- ✅ Easy to test with/without function calling
- ✅ Settings are clearly visible and accessible
- ✅ No need to modify code to change behavior
- ✅ Settings state visible in browser DevTools

### Performance
- ✅ Disabled features don't consume API calls
- ✅ Security filtering reduces search results
- ✅ Settings load instantly from localStorage
- ✅ No server-side storage needed

## 🎉 Integration with Existing Features

### Legacy Security Toggle
- The old security toggle in the header still works
- Both toggles are synchronized
- Changing one updates the other automatically

### Chat Functionality
- Settings are sent with every chat message
- Backend respects both security and function settings
- Agent adapts behavior based on settings

### Document Management
- Security setting affects document list API call
- Upload/delete operations respect security
- Owner-based permissions still enforced

## 📱 Mobile Responsive (Future Enhancement)

Current panel is 400px fixed width. For mobile:
- Consider full-width panel on small screens
- Maybe bottom sheet instead of side panel
- Touch-friendly toggle switches
- Swipe to close gesture

## 🔒 Security Considerations

### Client-Side Settings
- Settings stored in localStorage (client-side only)
- Not transmitted to server except during chat requests
- Can't be modified by other users
- Cleared when user clears browser data

### Server-Side Enforcement
- Backend validates all requests
- User ID always checked server-side
- Function calling permissions can be enforced server-side
- Settings are preferences, not security controls

## 🎨 Customization Options

Want to add more settings? Here's the pattern:

1. **Add HTML** in settings panel:
```html
<div class="settings-item">
    <label>
        <input type="checkbox" id="settingNewFeature" onchange="updateNewFeatureSetting()" checked>
        <div class="label-text">
            <div class="label-title">New Feature</div>
            <div class="label-desc">Description of what this feature does</div>
        </div>
    </label>
</div>
```

2. **Add JavaScript** functions:
```javascript
function getNewFeatureEnabled() {
    return localStorage.getItem('newFeature') === 'true';
}

function updateNewFeatureSetting() {
    const enabled = document.getElementById('settingNewFeature').checked;
    localStorage.setItem('newFeature', enabled);
    showSettingsStatus();
}
```

3. **Update loadSettingsState()**:
```javascript
function loadSettingsState() {
    document.getElementById('settingsEnableSecurity').checked = getSecurityEnabled();
    document.getElementById('settingsEnableFunctions').checked = getFunctionsEnabled();
    document.getElementById('settingNewFeature').checked = getNewFeatureEnabled(); // New!
}
```

4. **Add to ChatMessage** if needed:
```python
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    security_enabled: Optional[bool] = True
    enable_functions: Optional[bool] = True
    new_feature: Optional[bool] = False  # New setting
```

## 🎯 Next Steps

Possible enhancements:
- [ ] Export/import settings as JSON
- [ ] Settings presets (Power User, Privacy, Basic)
- [ ] Settings history/undo
- [ ] Admin-level settings (server-side)
- [ ] A/B testing different default values
- [ ] Settings sync across devices (requires backend)
- [ ] Dark mode toggle
- [ ] Language preferences
- [ ] Keyboard shortcuts configuration

## ✅ Test Checklist

Before considering this feature complete, test:
- [x] Settings panel opens/closes smoothly
- [x] Overlay appears and dismisses properly
- [x] Both toggles work and save to localStorage
- [x] Settings persist after page reload
- [x] Settings sync between panel and legacy toggles
- [x] Security toggle affects document list
- [x] Functions toggle affects agent behavior
- [x] Save notification appears and disappears
- [x] Panel works with different screen sizes
- [x] Clicking outside closes the panel
- [x] X button closes the panel
- [x] No JavaScript errors in console

## 📚 Related Documentation

- [INTEGRATION_ACTIONS.md](INTEGRATION_ACTIONS.md) - Details on integration features
- [MOCK_API_GUIDE.md](MOCK_API_GUIDE.md) - Mock API endpoints and usage
- [DEPLOYMENT_COMPLETE.md](DEPLOYMENT_COMPLETE.md) - Deployment summary and URLs

---

**Enjoy your new settings panel! 🎉**

Need help or want to customize further? Check the code in:
- **Frontend**: `src/main.py` (HTML/CSS/JavaScript section)
- **Backend**: `src/main.py` (ChatMessage model and chat endpoint)
- **Agent**: `src/agent/legal_agent.py` (chat method)
