export default [
  {
    title: 'Bảng Điều Khiển',
    to: { name: 'root' },
    icon: { icon: 'tabler-dashboard' },
    requireRole: ['user', 'admin'], // User and Admin can view
  },
  {
    title: 'Lương',
    to: { name: 'salary' },
    icon: { icon: 'tabler-currency-dong' },
    requireRole: ['user', 'admin'], // User and Admin can view
  },
  {
    title: 'Lịch Sử Lương',
    to: { name: 'salary-history' },
    icon: { icon: 'tabler-chart-line' },
    requireRole: ['user', 'admin'], // User and Admin can view
  },
  {
    title: 'Thành Tích',
    to: { name: 'achievements' },
    icon: { icon: 'tabler-trophy' },
    requireRole: ['user', 'admin'], // User and Admin can view
  },
  {
    title: 'Thưởng Năm',
    to: { name: 'year-bonus' },
    icon: { icon: 'tabler-gift' },
    requireRole: ['user', 'admin'], // User and Admin can view
  },
  {
    title: 'Đánh Giá',
    to: { name: 'evaluations' },
    icon: { icon: 'tabler-chart-bar' },
    requireRole: ['user', 'admin'], // User and Admin can view
  },
  {
    title: 'Hóa Đơn Ký Túc Xá',
    to: { name: 'dormitory-bills' },
    icon: { icon: 'tabler-home-dollar' },
    requireRole: ['user', 'admin'], // User and Admin can view
  },
  {
    title: 'Đồng Bộ Nhân Viên',
    to: { name: 'employee-sync' },
    icon: { icon: 'tabler-refresh' },
    requireRole: ['user', 'admin'], // User and Admin can view
  },
  {
    title: 'Quản Trị',
    icon: { icon: 'tabler-shield-lock' },
    requireRole: 'admin', // Only show for admin users
    children: [
      {
        title: 'Quản Lý Người Dùng',
        to: { name: 'user-manager' },
      },
      {
        title: 'Tìm Kiếm Nhân Viên',
        to: { name: 'employee-search' },
      },
      {
        title: 'Tải Lên Đánh Giá',
        to: { name: 'evaluation-upload' },
      },
      {
        title: 'Quản Lý PIDMS',
        to: { name: 'pidms-manager' },
      },
    ],
  },
]
