# Parts Tracker Application Suite

## Overview

The Parts Tracker is a comprehensive manufacturing tracking application suite built with Python and Tkinter. The application has been split into separate operator and admin interfaces while maintaining a shared database for seamless communication. It provides secure production scrap tracking, downtime monitoring, SMC (Sheet Moulding Compound) scrap recording, and comprehensive analytics for manufacturing environments.

## Architecture

The Parts Tracker suite consists of three main components:

1. **Operator Interface** (`parts_tracker_operator.py`) - Streamlined production floor interface
2. **Admin Interface** (`parts_tracker_admin.py`) - Comprehensive management and analytics interface
3. **Shared Database Module** (`shared_db.py`) - Common database operations and validation functions

This separated architecture allows:
- **Independent deployment** of operator and admin interfaces
- **Enhanced security** by separating user access levels
- **Optimized interfaces** tailored for specific user roles
- **Shared data consistency** through common database operations
- **Scalable deployment** in manufacturing environments

## Applications

### Operator Interface
**Purpose**: Production floor use by operators
**Features**:
- Clean, production-friendly interface
- Scrap entry recording
- Downtime logging
- SMC scrap tracking
- Order viewing and lookup
- Large, visible controls for production environment

### Admin Interface  
**Purpose**: Management and analytics by supervisors/administrators
**Features**:
- Secure authentication system
- Comprehensive operator analytics
- Downtime analysis and reporting
- SMC scrap analytics
- Operator management (add/remove)
- Order management
- System information and database statistics
- Detailed reporting capabilities

### Shared Database Module
**Purpose**: Common database operations for consistency
**Features**:
- Database initialization and management
- Input validation and sanitization
- Security functions (authentication, encryption)
- Common data operations
- Shared configuration and constants

## Getting Started

### Prerequisites
- Python 3.7 or higher
- Required Python packages (included with standard Python):
  - `sqlite3` (database operations)
  - `tkinter` (GUI framework)
  - `hashlib` (security functions)
  - `datetime` (time handling)
  - `re` (regular expressions)

### Installation

1. **Clone or download the repository:**
   ```bash
   git clone https://github.com/yourusername/partstracker.git
   cd partstracker
   ```

2. **Verify Python installation:**
   ```bash
   python --version
   ```

3. **No additional packages required** - all dependencies are included with standard Python installation.

### Quick Start

#### For Production Floor (Operators)
**Option 1: Use Batch File (Windows)**
```bash
# Double-click start_operator.bat
# OR run from command line:
start_operator.bat
```

**Option 2: Direct Python Execution**
```bash
python parts_tracker_operator.py
```

#### For Management (Administrators)
**Option 1: Use Batch File (Windows)**
```bash
# Double-click start_admin.bat  
# OR run from command line:
start_admin.bat
```

**Option 2: Direct Python Execution**
```bash
python parts_tracker_admin.py
```

### Default Admin Credentials
- **Username**: `FeuerWasser` | **Password**: `Jennifer124!`
- **Username**: `supervisor` | **Password**: `super456`

## File Structure

```
partstracker/
├── shared_db.py                  # Shared database operations and validation
├── parts_tracker_operator.py     # Operator interface application
├── parts_tracker_admin.py        # Admin interface application
├── start_operator.bat           # Windows batch file for operator app
├── start_admin.bat             # Windows batch file for admin app
├── parts_tracker_cli.py        # Legacy CLI version (full features)
├── pparts tracker.py           # Legacy monolithic GUI version
├── README.md                   # This documentation
├── LICENSE                     # License file
└── parts_tracker.db          # SQLite database (created automatically)
```

## Usage Guide

### Operator Interface Usage

#### Recording Production Scrap
1. Open operator interface
2. Navigate to "Scrap Entry" tab
3. Enter operator number, select part number and scrap reason
4. Input order number and scrap count
5. Click "Record Scrap Entry"

#### Logging Downtime
1. Navigate to "Downtime Entry" tab
2. Enter operator number
3. Select downtime reason from dropdown
4. Input duration in minutes (1-480 minutes)
5. Click "Record Downtime Entry"

#### Recording SMC Scrap
1. Navigate to "SMC Scrap Entry" tab
2. Enter operator number and part type
3. Select SMC scrap reason
4. Input scrap count
5. Click "Record SMC Scrap Entry"

#### Viewing Orders
1. Navigate to "View Orders" tab
2. Click "Refresh Orders" to see current orders
3. Use order lookup to find specific orders by number

### Admin Interface Usage

#### Accessing Admin Features
1. Launch admin interface
2. Login with admin credentials
3. Navigate between tabs for different functions

#### Viewing Analytics
1. Navigate to "Analytics Dashboard" tab
2. Click "Refresh Analytics" for latest data
3. View comprehensive operator performance metrics
4. Enter operator number for detailed analytics

#### Managing Operators
1. Navigate to "Operator Management" tab
2. Add operators: Enter number and name, click "Add Operator"
3. Remove operators: Enter number, click "Remove Operator"
4. View current operators in the list

#### Managing Orders
1. Navigate to "Order Management" tab
2. Create orders: Select part number, enter quantity, click "Create Order"
3. View recent orders in the list
4. Refresh list as needed

## Core Features

### Production Scrap Tracking
- Record and track production scrapping with detailed reason codes
- Support for multiple part numbers and order tracking
- Real-time entry validation

### Downtime Monitoring
- Log operator downtime with comprehensive reason tracking
- Duration validation (1-480 minutes per entry)
- Shift-based tracking and reporting

### SMC Scrap Recording
- Track Sheet Moulding Compound scrap with specialized reason codes
- Part type flexibility for diverse manufacturing needs
- Dedicated SMC analytics and reporting

### Order Management
- Create and manage production orders
- Real-time order status tracking
- Integration with scrap tracking system

### Operator Management
- Add and remove operators with privacy protection
- Anonymized operator tracking for GDPR compliance
- Secure operator data handling

## Security & Privacy

### Authentication Security
- **Secure Authentication**: SHA-256 password hashing with brute force protection
- **Account Lockout**: Automatic lockout after failed login attempts (15-minute lockout)
- **Login Monitoring**: All login attempts logged for security analysis
- **Session Management**: Secure session handling in admin interface

### Data Privacy
- **Privacy Protection**: Operator names are hashed and anonymized for privacy
- **Data Anonymization**: Display names use partial hashes for identification
- **GDPR Compliance**: Privacy-by-design architecture

### Input Security
- **Input Validation**: Comprehensive sanitization prevents injection attacks
- **SQL Injection Prevention**: Parameterized queries throughout
- **XSS Protection**: Input sanitization for all user data
- **Length Validation**: Maximum input lengths enforced

## Analytics & Reporting

### Operator Analytics
- **Performance Tracking**: Efficiency metrics and productivity analysis
- **Scrap Analysis**: Total scrap counts and efficiency percentages
- **Work Distribution**: Orders worked and production volume tracking
- **Historical Trends**: Time-based performance analysis

### Downtime Analysis
- **Event Tracking**: Total downtime events and duration monitoring
- **Reason Analysis**: Breakdown by downtime categories
- **Efficiency Impact**: Downtime's effect on productivity
- **Shift Analysis**: Day-level downtime aggregation

### SMC Scrap Analytics
- **Quality Tracking**: SMC scrap counts and reasons analysis
- **Part Type Analysis**: Scrap tracking by part type
- **Trend Monitoring**: Daily averages and pattern identification
- **Quality Improvement**: Data-driven quality insights

## Data Insights

### Scrap Reasons Tracked
- **Production**: foreign material, smear, chip, burn, light, heavy, crack, no fill
- **SMC**: incomplete fill, flash/excess material, air bubbles/voids, surface defects,
  dimensional out of spec, fiber showing, delamination, warp/distortion, gel coat defects,
  contamination, burn marks, under cure, over cure, crack/split, poor surface finish, other

### Downtime Categories  
- machine breakdown, material shortage, quality hold, maintenance, setup/changeover,
  training, meeting, break, lunch, waiting for work, tooling issue, power outage, other

### Part Numbers Supported
- 780208, 780508, 780108, 780308, 780608 (configurable in shared_db.py)

## Database Schema

The application uses SQLite with the following tables:

### Core Tables
- **`operators`**: Operator information (anonymized for privacy)
- **`orders`**: Production orders and tracking
- **`scrap_entries`**: Production scrap logging
- **`downtime_entries`**: Operator downtime tracking
- **`smc_scrap_entries`**: SMC (Sheet Moulding Compound) scrap tracking

### Security Tables
- **`admin_credentials`**: Hashed admin authentication data
- **`login_attempts`**: Security monitoring and audit logging

## Deployment Recommendations

### Production Floor Deployment
1. Deploy `parts_tracker_operator.py` on production terminals
2. Use `start_operator.bat` for easy access
3. Configure terminals for auto-login to operator interface
4. Ensure database file is accessible to all terminals

### Management Office Deployment  
1. Deploy `parts_tracker_admin.py` on management computers
2. Use `start_admin.bat` for easy access
3. Secure admin credentials appropriately
4. Regular database backups recommended

### Network Deployment
1. Place `shared_db.py` and database file on shared network location
2. Update file paths in applications if needed
3. Ensure all terminals have network access to database
4. Consider database locking for concurrent access

## Troubleshooting

### Common Issues

**"shared_db.py module not found" Error**
- Ensure all three main files are in same directory
- Check file permissions
- Verify Python path if running from different directory

**Database Access Issues**
- Check file permissions on `parts_tracker.db`
- Ensure SQLite is available (should be with standard Python)
- Verify disk space for database growth

**Login Issues (Admin)**
- Use default credentials: FeuerWasser/Jennifer124! or supervisor/super456
- Wait 15 minutes if account is locked from failed attempts
- Check for caps lock or keyboard layout issues

**Interface Display Issues**
- Ensure Tkinter is available (standard with Python)
- Try running with admin privileges if needed
- Check display scaling if interface appears too large/small

### Performance Optimization
- **Regular Database Maintenance**: Consider periodic cleanup of old entries
- **Index Management**: Database includes performance indexes
- **Memory Usage**: Applications designed for minimal memory footprint
- **Concurrent Access**: Database handles multiple simultaneous users

## Legacy Applications

The repository includes legacy versions for reference:
- **`pparts tracker.py`**: Original monolithic GUI application
- **`parts_tracker_cli.py`**: Command-line interface version

These are maintained for backward compatibility but new deployments should use the separated architecture.

## Technical Notes

### Database Design
- **Referential Integrity**: Foreign key constraints where appropriate
- **Data Validation**: Multi-layer validation (application + database)
- **Performance Indexes**: Optimized for common query patterns
- **Scalability**: Designed for typical manufacturing scale (hundreds of operators)

### Security Implementation
- **Password Storage**: SHA-256 hashing with no plaintext storage
- **Session Security**: Time-based session management
- **Audit Logging**: Comprehensive activity tracking
- **Input Sanitization**: Multi-layer validation and sanitization

### Privacy Compliance
- **Data Minimization**: Only necessary data collected
- **Anonymization**: Operator data anonymized for display
- **Access Control**: Role-based access separation
- **Audit Trail**: Complete activity logging for compliance

## Support & Maintenance

### Regular Maintenance
1. **Database Backups**: Regular backup of `parts_tracker.db`
2. **Log Monitoring**: Review login attempts for security
3. **Performance Monitoring**: Check application response times
4. **User Training**: Ongoing training for new operators/admins

### Updates & Modifications
1. **Configuration Changes**: Edit `shared_db.py` for settings
2. **New Part Numbers**: Update `part_numbers` list in `shared_db.py`  
3. **New Scrap Reasons**: Update reason lists in `shared_db.py`
4. **Interface Customization**: Modify individual application files

### Data Export
The SQLite database can be accessed with standard database tools for:
- **Reporting**: Custom reports using SQL queries
- **Data Export**: CSV, Excel export using database tools
- **Integration**: Connection to ERP/MES systems
- **Analysis**: Business intelligence tool integration

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request with detailed description

## Contact

For support, questions, or contributions, please contact the development team or create an issue in the repository.

---

**Parts Tracker Application Suite** - Built for manufacturing excellence with security and privacy by design.