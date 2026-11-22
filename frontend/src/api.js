import axios from 'axios'

export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
export const api = axios.create({ baseURL: API_BASE, timeout: 120000 })

export function getErrorMessage(error) {
  return error?.response?.data?.detail || error?.message || 'Something went wrong.'
}
