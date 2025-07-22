# 📋 ProjectFlow - Hệ thống Quản lý Dự án

**ProjectFlow** là một ứng dụng web quản lý dự án được xây dựng bằng Django, giúp các đội nhóm tổ chức, theo dõi và hoàn thành công việc một cách hiệu quả.

## ✨ Tính năng chính

### 🔐 Quản lý người dùng
- Đăng ký và đăng nhập với hệ thống xác thực tùy chỉnh
- Quản lý hồ sơ người dùng
- Theo dõi hoạt động của người dùng

### 📊 Quản lý dự án
- **Tạo và quản lý dự án**: Tạo dự án mới với mô tả chi tiết
- **Trạng thái dự án**: Active, Completed, On Hold
- **Phân quyền**: Owner, Admin, Member với các quyền khác nhau
- **Lời mời tham gia**: Gửi lời mời qua email với thời hạn

### ✅ Quản lý công việc (Tasks)
- **Tạo và phân công công việc** cho các thành viên
- **Trạng thái công việc**: Todo, In Progress, Done
- **Độ ưu tiên**: Low, Medium, High
- **Bình luận**: Thảo luận và cập nhật trên từng công việc

### 👥 Cộng tác nhóm
- Quản lý thành viên dự án
- Hệ thống lời mời tham gia dự án
- Bình luận và tương tác trên công việc

## 🛠 Công nghệ sử dụng

- **Backend**: Django 5.2
- **Database**: SQLite3 (có thể thay đổi sang PostgreSQL/MySQL)
- **Frontend**: HTML5, CSS3, Django Templates
- **Authentication**: Django Custom User Model
- **Timezone**: Asia/Ho_Chi_Minh
- **Language**: Tiếng Việt

## 📁 Cấu trúc dự án

```
projectflow/
├── dashboard/              # Ứng dụng quản lý dự án chính
│   ├── models.py          # Models: Project, Task, Comment, ProjectMember
│   ├── views.py           # Views xử lý logic nghiệp vụ
│   └── urls.py            # URL routing cho dashboard
├── users/                 # Ứng dụng quản lý người dùng
│   ├── models.py          # Custom User model
│   ├── views.py           # Đăng ký, đăng nhập
│   └── forms.py           # Form đăng ký người dùng
├── templates/             # Templates HTML
│   ├── base.html          # Template cơ bản
│   ├── dashboard/         # Templates cho dashboard
│   └── users/             # Templates cho user
├── static/                # Files CSS, JS, images
└── projectflow/           # Cấu hình Django chính
    ├── settings.py        # Cấu hình dự án
    └── urls.py            # URL routing chính
```

## 🚀 Cài đặt và chạy dự án

### Yêu cầu hệ thống
- Python 3.8+
- Django 5.2+
- SQLite3 (hoặc PostgreSQL/MySQL)

### Hướng dẫn cài đặt

1. **Clone dự án**
```bash
git clone https://github.com/QuocKhanhh123/ProjectFlow.git
cd projectflow
```

2. **Tạo môi trường ảo**
```bash
python -m venv env
source env/bin/activate  # Trên Windows: env\Scripts\activate
```

3. **Cài đặt dependencies**
```bash
pip install django
```

4. **Chạy migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Tạo superuser (tùy chọn)**
```bash
python manage.py createsuperuser
```

6. **Chạy server development**
```bash
python manage.py runserver
```

7. **Truy cập ứng dụng**
- Trang chủ: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/
- Dashboard: http://127.0.0.1:8000/overview/
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request


---
⭐ **Nếu dự án này hữu ích cho bạn, hãy cho một star trên GitHub!** 
