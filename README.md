# Parts Tracker

A comprehensive manufacturing production tracking system designed for automotive and composite manufacturing environments. Track production scrap, SMC (Sheet Moulding Compound) scrap, operator downtime, and generate detailed analytics.

## 🏭 Overview

Parts Tracker is a dual-interface application (GUI and CLI) designed for manufacturing facilities to track production efficiency, scrap rates, downtime events, and operator performance. Originally designed for automotive composite manufacturing, it features specialized SMC (Sheet Moulding Compound) tracking for parts like hood panels, bumper covers, and door panels.

## ✨ Features

### 📊 Production Tracking
- **Scrap Tracking**: Log production scrap with detailed reasons (foreign material, smear, chip, burn, etc.)
- **SMC (Sheet Moulding Compound) Scrap**: Specialized tracking for composite manufacturing defects (incomplete fill, flash/excess material, air bubbles, fiber showing, etc.)
- **Downtime Logging**: Track operator downtime with categorized reasons (mechanical issues, material shortage, training, etc.)
- **Order Management**: Create and track production orders with part numbers and quantities

### 👥 User Management
- **Operator Interface**: Streamlined interface for production floor workers
- **Administrator Interface**: Comprehensive management and analytics dashboard
- **Secure Authentication**: SHA-256 hashed credentials with brute force protection
- **Privacy Protection**: Anonymized operator data with secure storage

### 📈 Analytics & Reporting
- **Operator Analytics**: Performance metrics, efficiency tracking, and scrap rate analysis
- **Detailed Reports**: Individual operator deep-dive analytics with historical trends
- **Real-time Data**: Live tracking of production metrics and downtime events
- **Shift Reporting**: Daily and shift-based analytics for production planning

### 🔒 Security Features
- **Secure Authentication**: Multi-layer security with hashed credentials
- **Brute Force Protection**: Account lockout after failed login attempts
- **Input Validation**: Comprehensive sanitization against injection attacks
- **Audit Logging**: Complete login attempt and activity tracking

## 🚀 Getting Started

### Prerequisites
- Python 3.7 or higher
- Required Python packages:
  - `sqlite3` (included with Python)
  - `tkinter` (included with Python - for GUI version)
  - `hashlib` (included with Python)
  - `datetime` (included with Python)
  - `re` (included with Python)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/partstracker.git
   cd partstracker
   ```

2. **Run the application:**
   
   **GUI Version:**
   ```bash
   python "pparts tracker.py"
   ```
   
   **CLI Version:**
   ```bash
   python parts_tracker_cli.py
   ```

3. **First-time setup:**
   - The application will automatically initialize the SQLite database
   - Default admin accounts are created:
     - Username: `FeuerWasser`, Password: `Jennifer124!`
     - Username: `supervisor`, Password: `super456`

## 💻 Usage

### GUI Application (`pparts tracker.py`)

The GUI version provides a full-featured graphical interface with:

**Login Screen:**
- Secure operator or administrator login
- Automatic account lockout protection

**Operator Interface:**
- Track regular scrap entries
- Log SMC (Sheet Moulding Compound) scrap
- Record downtime events
- View personal activity history

**Administrator Interface:**
- Create and manage production orders
- View comprehensive operator analytics
- Add/remove operators from the system
- Access detailed performance reports
- Monitor all system activity

### CLI Application (`parts_tracker_cli.py`)

The command-line version offers the same functionality through a text-based menu system:

**Admin Menu:**
1. Create new orders
2. View recent scrap entries
3. View operator analytics
4. View detailed operator analytics
5. Manage operators
6. View downtime entries
7. View SMC scrap entries
8. Exit

**Operator Menu:**
1. Track scrap for existing orders
2. Track downtime
3. Track SMC scrap
4. View personal scrap entries
5. View personal downtime entries
6. View personal SMC scrap entries
7. Exit

## 🗄️ Database Schema

The application uses SQLite with the following tables:

- **`scrap_entries`**: Regular production scrap tracking
- **`smc_scrap_entries`**: SMC (Sheet Moulding Compound) specific scrap
- **`downtime_entries`**: Operator downtime events
- **`operators`**: Operator management (with hashed names)
- **`orders`**: Production order tracking
- **`admin_credentials`**: Secure administrator authentication
- **`login_attempts`**: Security audit logging

## 🎯 Manufacturing Focus

### SMC (Sheet Moulding Compound) Manufacturing

Specialized features for composite manufacturing:

**Part Types:**
- Hood panels
- Door panels
- Bumper covers
- Fender assemblies
- And other automotive composite parts

**SMC Scrap Reasons:**
- Incomplete fill
- Flash/excess material
- Air bubbles/voids
- Surface defects
- Dimensional out of spec
- Fiber showing
- Delamination
- Warp/distortion
- Contamination
- Cure issues
- Tool marks
- Gelcoat defects
- Resin starved areas
- Overpacking
- Sink marks
- Cracking

### Production Tracking

**Regular Scrap Reasons:**
- Foreign material
- Smear
- Chip
- Burn
- Light
- Heavy
- Crack
- No fill

**Downtime Categories:**
- Mechanical issues
- Material shortage
- Quality hold
- Maintenance
- Setup/changeover
- Training
- Meeting
- Break
- Lunch
- Waiting for work
- Tooling issues
- Power outage
- Other

## 📊 Analytics Features

### Operator Performance Metrics
- Total parts produced
- Scrap rates and trends
- Efficiency percentages
- Downtime analysis
- Part type specialization
- Historical performance tracking

### Management Dashboards
- Real-time production monitoring
- Cross-operator comparisons
- Shift performance analysis
- Quality trend identification
- Resource utilization tracking

## 🔧 Configuration

### Default Settings
- Maximum operator number: 9999
- Downtime duration limit: 480 minutes (8 hours)
- Scrap count limit: 999,999 parts
- Login attempt limit: 5 attempts
- Account lockout duration: 15 minutes

### Customization
The application can be customized by modifying the following in the source code:
- Scrap reason lists
- Part number configurations
- Validation limits
- Security parameters

## 🛡️ Security

### Data Protection
- **Password Hashing**: SHA-256 encryption for all credentials
- **Input Sanitization**: Comprehensive validation against SQL injection
- **Session Management**: Secure login state handling
- **Audit Trails**: Complete logging of all system access

### Privacy Features
- **Anonymized Data**: Operator names are hashed for privacy
- **Secure Storage**: All sensitive data encrypted in database
- **Access Control**: Role-based permissions (Operator vs Administrator)

## 📁 File Structure

```
partstracker/
├── pparts tracker.py          # Main GUI application
├── parts_tracker_cli.py       # Command-line interface
├── parts_tracker.db          # SQLite database (created on first run)
├── orders_data.json          # Order configuration data
├── README.md                 # This documentation
├── LICENSE                   # License information
└── test files/               # Testing and debugging scripts
    ├── test_app.py
    ├── test_functionality.py
    ├── test_simple.py
    └── debug_test.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For technical support or questions:
- Create an issue in this repository
- Check the [wiki](../../wiki) for detailed documentation
- Review the source code comments for implementation details

## 📋 Changelog

### Latest Version
- ✅ Complete SMC (Sheet Moulding Compound) tracking system
- ✅ Comprehensive downtime tracking and analytics
- ✅ Enhanced security with brute force protection
- ✅ Full CLI interface with feature parity
- ✅ Updated terminology for manufacturing accuracy
- ✅ Comprehensive analytics dashboard
- ✅ Privacy-focused operator management

---

**Built for modern manufacturing environments with a focus on quality, security, and comprehensive production tracking.**