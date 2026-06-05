import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import logo from '../assets/ep-logo.png'
import { NAV_ORDER, neighbors } from '../chapters'
import { HIER_BAR_CSS } from '../components/HierBar'

// Shell de la SPA unificada: barra superior con la marca EP, el menú de
// secciones (NAV_ORDER) y el contenido vía <Outlet/>. Al pie, un pager
// prev/next que recorre el mismo orden de navegación.
export default function Layout() {
  const { pathname } = useLocation()
  const { prev, next } = neighbors(pathname)

  return (
    <>
      {/* CSS de las barras horizontales (BarList), global para todas las páginas
          que lo usan (jerarquía, instrumentos, Mercado Público…). */}
      <style>{HIER_BAR_CSS}</style>
      <header className="topbar">
        {/* Marca centrada: logo EP sobre fondo claro + título del explorador */}
        <Link to="/" className="brand">
          <img src={logo} alt="Espacio Público" />
          <span className="brand-t">
            Inclusión sostenible de medicamentos en los planes de salud en Chile
            <span className="brand-sub">Gasto en medicamentos en Chile · explorador de datos</span>
          </span>
        </Link>
        {/* Menú de secciones */}
        <nav className="topnav">
          {NAV_ORDER.map(c => (
            <NavLink
              key={c.route}
              to={c.route}
              end={c.route === '/'}
              className={({ isActive }) => (isActive ? 'active' : undefined)}
            >
              {c.num ? `${c.num}. ` : ''}{c.short ?? c.title}
            </NavLink>
          ))}
        </nav>
        <div className="rainbow" />
      </header>

      <div className="layout">
        <main>
          <Outlet />

          {/* Pager prev/next: recorre el mismo orden que el menú */}
          {(prev || next) && (
            <nav className="pagernav">
              {prev && (
                <Link to={prev.route} className="pager prev">
                  <span className="arrow" aria-hidden>‹</span>
                  <span className="pl">
                    <span className="dir">Anterior</span>
                    <span className="pt">{prev.num ? `${prev.num}. ` : ''}{prev.title}</span>
                  </span>
                </Link>
              )}
              {next && (
                <Link to={next.route} className="pager next">
                  <span className="pl">
                    <span className="dir">Siguiente</span>
                    <span className="pt">{next.num ? `${next.num}. ` : ''}{next.title}</span>
                  </span>
                  <span className="arrow" aria-hidden>›</span>
                </Link>
              )}
            </nav>
          )}
        </main>
      </div>
    </>
  )
}
