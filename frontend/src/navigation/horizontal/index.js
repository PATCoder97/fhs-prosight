export default [
  {
    title: 'Home',
    to: { name: 'root' },
    icon: { icon: 'tabler-smart-home' },
  },
  {
    title: 'Second page',
    to: { name: 'second-page' },
    icon: { icon: 'tabler-file' },
  },
  {
    title: 'Salary',
    to: { name: 'salary' },
    icon: { icon: 'tabler-currency-dong' },
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
    title: 'Admin',
    icon: { icon: 'tabler-shield-lock' },
    requireRole: 'admin', // Only show for admin users
    children: [
      {
        title: 'User Manager',
        to: { name: 'user-manager' },
        icon: { icon: 'tabler-users-group' },
      },
    ],
  },
]
