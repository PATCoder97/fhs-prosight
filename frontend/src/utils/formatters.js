/**
 * Shared formatting utility functions
 */

/**
 * Auto-format Employee ID: "14732" → "VNW0014732"
 * @param {string|number} input - The employee ID input
 * @returns {string} - Formatted employee ID
 */
export const formatEmployeeId = (input) => {
  if (!input) return ''

  // Remove whitespace
  const cleaned = input.toString().trim()

  // If already starts with VNW, return as-is
  if (cleaned.toUpperCase().startsWith('VNW')) {
    return cleaned.toUpperCase()
  }

  // If just numbers, format as VNW + padded numbers
  if (/^\d+$/.test(cleaned)) {
    const paddedNumber = cleaned.padStart(7, '0')
    return `VNW${paddedNumber}`
  }

  // Otherwise return as-is
  return cleaned
}

/**
 * Format currency amount in Vietnamese Dong
 * @param {number} amount - The amount to format
 * @returns {string} - Formatted currency string
 */
export const formatCurrency = (amount) => {
  if (!amount && amount !== 0) return '0 ₫'
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND',
  }).format(amount)
}

/**
 * Get score color based on evaluation score
 * @param {string} score - The evaluation score
 * @returns {string} - Vuetify color name
 */
export const getScoreColor = (score) => {
  if (!score) return 'default'
  switch (score) {
    case '優': return '#D48DFF'    // Tốt - Xanh lá
    case '良': return '#00E5FF'       // Khá - Xanh dương
    case '甲':                     // Trung Bình - Primary
    case '甲上':                   // Trung Bình Trên - Primary
    case '甲下':                   // Trung Bình Dưới - Primary
      return 'primary'
    case '乙': return '#FF4C51'    // Yếu - Vàng
    case '丙': return 'error'      // Kém - Đỏ
    default: return 'default'
  }
}

/**
 * Get score label in Vietnamese
 * @param {string} score - The evaluation score
 * @returns {string} - Vietnamese label
 */
export const getScoreLabel = (score) => {
  const labels = {
    '優': 'Tốt',
    '良': 'Khá',
    '甲': 'Trung Bình',
    '甲上': 'Trung Bình Khá',
    '甲下': 'Trung Bình Yếu',
    '乙': 'Yếu',
    '丙': 'Kém',
  }
  return labels[score] || score
}

/**
 * Get score icon based on evaluation score
 * @param {string} score - The evaluation score
 * @returns {string} - Tabler icon name
 */
export const getScoreIcon = (score) => {
  if (score === '優') return 'tabler-trophy'
  if (score === '良') return 'tabler-medal'
  if (score === '甲') return 'tabler-award'
  if (score === '乙') return 'tabler-star'
  return 'tabler-circle'
}
