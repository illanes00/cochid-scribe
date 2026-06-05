import { HashRouter, Routes, Route, useLocation } from 'react-router-dom'
import { useEffect } from 'react'
import Layout from './layout/Layout'
import Home from './pages/Home'
import CapJerarquia from './pages/CapJerarquia'
import CapMedicamento from './pages/CapMedicamento'
import CapExplorador from './pages/CapExplorador'
import CapInstrumentos from './pages/CapInstrumentos'
import CapSintesis from './pages/CapSintesis'
import CapMarco from './pages/CapMarco'
import CapChile from './pages/CapChile'
import Fuentes from './pages/Fuentes'
import CapEsqueleto from './pages/CapEsqueleto'

// Al navegar, llevar el scroll al tope.
function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])
  return null
}

// Capítulo 6 · Marco: el marco SHA (definiciones y taxonomía) seguido del gasto
// en salud total y la comparabilidad OCDE-Chile, como una sola capa de referencia.
function CapMarcoReferencia() {
  return (
    <>
      <CapMarco />
      <CapChile />
    </>
  )
}

// SPA unificada: portada + seis capítulos del recorrido + dos secciones de
// referencia (fuentes/modelo de datos y esqueleto lógico). HashRouter para que
// el deep-link funcione bajo el subpath estático donde se sirve la app.
export default function App() {
  return (
    <HashRouter>
      <ScrollToTop />
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Home />} />
          <Route path="/jerarquia" element={<CapJerarquia />} />
          <Route path="/medicamento" element={<CapMedicamento />} />
          <Route path="/explorador" element={<CapExplorador />} />
          <Route path="/instrumentos" element={<CapInstrumentos />} />
          <Route path="/comparacion" element={<CapSintesis />} />
          <Route path="/marco" element={<CapMarcoReferencia />} />
          <Route path="/fuentes" element={<Fuentes />} />
          <Route path="/esqueleto" element={<CapEsqueleto />} />
          <Route path="*" element={<Home />} />
        </Route>
      </Routes>
    </HashRouter>
  )
}
