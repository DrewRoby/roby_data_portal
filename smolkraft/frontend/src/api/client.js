import axios from 'axios'

function getCsrfToken() {
  return document.cookie
    .split('; ')
    .find(row => row.startsWith('csrftoken='))
    ?.split('=')[1]
}

const client = axios.create({
  baseURL: '/smolkraft/api',
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.request.use(config => {
  const token = getCsrfToken()
  if (token) config.headers['X-CSRFToken'] = token
  return config
})

export default client
