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
