import axios from 'axios'
import { useAuthStore } from '../store/authStore'

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api' })

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) config.headers.Authorization = `Token ${token}`
  return config
})

export default api
