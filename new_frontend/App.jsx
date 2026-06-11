import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { LangProvider } from './context/LangContext'
import ProtectedRoute from './components/ProtectedRoute'

import Login        from './pages/Login'
import ManagerLayout from './layouts/ManagerLayout'
import DriverLayout  from './layouts/DriverLayout'

import Vehicles from './pages/manager/Vehicles'
import Drivers  from './pages/manager/Drivers'
import Trips    from './pages/manager/Trips'
import BulkCalc from './pages/manager/BulkCalc'
import { MyTrips, LogTrip } from './pages/driver/DriverPages'

export default function App() {
  return (
    <LangProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />

            {/* Manager routes */}
            <Route
              path="/manager"
              element={
                <ProtectedRoute requireManager>
                  <ManagerLayout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Navigate to="vehicles" replace />} />
              <Route path="vehicles" element={<Vehicles />} />
              <Route path="drivers"  element={<Drivers />} />
              <Route path="trips"    element={<Trips />} />
              <Route path="bulk"     element={<BulkCalc />} />
            </Route>

            {/* Driver routes */}
            <Route
              path="/driver"
              element={
                <ProtectedRoute>
                  <DriverLayout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Navigate to="trips" replace />} />
              <Route path="trips" element={<MyTrips />} />
              <Route path="log"   element={<LogTrip />} />
            </Route>

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </LangProvider>
  )
}
