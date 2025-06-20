# FreightLink - Freight Management System

A comprehensive Django-based freight management platform that connects shippers with carriers, streamlining the logistics and transportation process.

## 🚚 Overview

FreightLink is a modern web application designed to facilitate freight booking, bidding, and management. The platform provides an intuitive interface for both shippers and carriers to manage their logistics operations efficiently.

## ✨ Features

### Core Functionality
- **User Authentication & Authorization** - Secure user registration and login system
- **Freight Booking Management** - Create, manage, and track freight bookings
- **Bidding System** - Competitive bidding platform for carriers
- **Truck Management** - Register and manage truck fleets
- **Real-time Messaging** - Communication between shippers and carriers
- **Dashboard Analytics** - Comprehensive overview of operations
- **Support System** - Built-in help and support features

### User Roles
- **Shippers** - Post freight requirements and manage bookings
- **Carriers** - Browse available freight and submit bids
- **Administrators** - Manage platform operations and users

## 🏗️ System Architecture

### Backend Structure
```
freightlink_backend/
├── accounts/          # User authentication and profiles
├── bids/             # Bidding system and management
├── bookings/         # Freight booking operations
├── cargo/            # Cargo management and tracking
├── dashboard/        # Dashboard and analytics
├── messaging/        # Real-time communication
├── support/          # Help and support system
├── trucks/           # Vehicle fleet management
└── Templates/        # Frontend templates
```

## 🛠️ Technologies Used

### Backend
- **Django 4.x** - Web framework
- **Django REST Framework** - API development
- **SQLite** - Database (development)
- **Python 3.10+** - Programming language

### Frontend
- **HTML5** - Markup
- **CSS3** - Styling
- **JavaScript** - Interactive functionality
- **Bootstrap** - Responsive design framework

## 🚀 Getting Started

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/freightlink-backend.git
   cd freightlink-backend
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   DATABASE_URL=sqlite:///db.sqlite3
   ```

5. **Run database migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   Open your browser and navigate to `http://localhost:8000`

## 📱 Usage

### For Shippers
1. Register an account or log in
2. Post freight requirements
3. Review and accept bids from carriers
4. Track shipment progress
5. Manage payments and documentation

### For Carriers
1. Create a carrier account
2. Register your trucks and fleet
3. Browse available freight opportunities
4. Submit competitive bids
5. Manage accepted jobs and deliveries

### For Administrators
1. Access admin panel at `/admin`
2. Manage users and permissions
3. Monitor platform activity
4. Handle support requests
5. Generate reports and analytics

## 🔧 API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout

### Bookings
- `GET /api/bookings/` - List all bookings
- `POST /api/bookings/` - Create new booking
- `GET /api/bookings/{id}/` - Get booking details
- `PUT /api/bookings/{id}/` - Update booking

### Bids
- `GET /api/bids/` - List bids
- `POST /api/bids/` - Submit bid
- `GET /api/bids/{id}/` - Get bid details

### Trucks
- `GET /api/trucks/` - List trucks
- `POST /api/trucks/` - Register truck
- `PUT /api/trucks/{id}/` - Update truck info

## 🗂️ Project Structure

```
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
├── .gitignore               # Git ignore rules
├── README.md                # Project documentation
├── DEVLOG.md               # Development log
├── db.sqlite3              # SQLite database
├── freight_app.log         # Application logs
├── freightlink_backend/    # Main Django project
│   ├── settings.py         # Django settings
│   ├── urls.py            # URL configuration
│   ├── wsgi.py            # WSGI configuration
│   └── asgi.py            # ASGI configuration
├── Templates/              # HTML templates
├── accounts/              # User management app
├── bids/                 # Bidding system app
├── bookings/             # Booking management app
├── cargo/                # Cargo tracking app
├── dashboard/            # Dashboard app
├── messaging/            # Communication app
├── support/              # Support system app
└── trucks/               # Fleet management app
```

## 🚧 Development Status

This project is currently in active development. Key features implemented:

- ✅ User authentication system
- ✅ Basic booking management
- ✅ Bidding functionality
- ✅ Truck registration
- ✅ Messaging system
- ✅ Dashboard interface
- 🔄 Payment integration (in progress)
- 🔄 Advanced analytics (planned)
- 🔄 Mobile app (planned)

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 coding standards
- Write descriptive commit messages
- Add tests for new features
- Update documentation as needed

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file 

### Version 2.0 (Planned)
- [ ] Mobile application (React Native)
- [ ] Advanced route optimization
- [ ] Integration with mapping services
- [ ] Multi-language support
- [ ] Enhanced reporting and analytics



## 📊 Screenshots

*Screenshots will be added as the UI development progresses*

## 🙏 Acknowledgments

- Django community for the excellent framework
- Contributors and testers
- Open source libraries used in this project

---


*Last updated: June 2025*
