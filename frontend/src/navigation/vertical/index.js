export default [
  {
    title: 'HRS Dashboard',
    to: { name: 'root' },
    icon: { icon: 'tabler-dashboard' },
    requireRole: ['user', 'admin'], // User and Admin can view
  },
  {
    title: 'Salary',
    to: { name: 'salary' },
    icon: { icon: 'tabler-currency-dong' },
    requireRole: ['user', 'admin'], // User and Admin can view
  },
  {
    title: 'Salary History',
    to: { name: 'salary-history' },
    icon: { icon: 'tabler-chart-line' },
    requireRole: ['user', 'admin'], // User and Admin can view
  },
  {
    title: 'Achievements',
    to: { name: 'achievements' },
    icon: { icon: 'tabler-trophy' },
    requireRole: ['user', 'admin'], // User and Admin can view
  },
  {
    title: 'Year Bonus',
    to: { name: 'year-bonus' },
    icon: { icon: 'tabler-gift' },
    requireRole: ['user', 'admin'], // User and Admin can view
  },
  {
    title: 'Evaluations',
    to: { name: 'evaluations' },
    icon: { icon: 'tabler-chart-bar' },
    requireRole: ['user', 'admin'], // User and Admin can view
  },
  {
    title: 'Dormitory Bills',
    to: { name: 'dormitory-bills' },
    icon: { icon: 'tabler-home-dollar' },
    requireRole: ['user', 'admin'], // User and Admin can view
  },
  {
    title: 'Employee Sync',
    to: { name: 'employee-sync' },
    icon: { icon: 'tabler-refresh' },
    requireRole: ['user', 'admin'], // User and Admin can view
  },
  {
    title: 'Admin',
    icon: { icon: 'tabler-shield-lock' },
    requireRole: 'admin', // Only show for admin users
    children: [
      {
        title: 'User Manager',
        to: { name: 'user-manager' },
      },
      {
        title: 'Employee Search',
        to: { name: 'employee-search' },
      },
      {
        title: 'Evaluation Upload',
        to: { name: 'evaluation-upload' },
      },
    ],
  },
]
