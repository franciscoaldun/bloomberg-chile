# Bloomberg Chile — Panel Económico Abierto

**Un terminal financiero gratuito y de código abierto para visualizar la economía chilena en tiempo real.**

Datos directos del Banco Central de Chile. Sin intermediarios. Sin suscripción. Sin paywall.

![Python](https://img.shields.io/badge/Python-FastAPI-009688?style=flat-square)
![Next.js](https://img.shields.io/badge/Next.js-React-000?style=flat-square)
![License](https://img.shields.io/badge/Licencia-NonCommercial-red?style=flat-square)
![Chile](https://img.shields.io/badge/Hecho%20en-Chile-0033A0?style=flat-square)

---

## ¿Por qué existe esto?

La economía no debería ser un privilegio de académicos, analistas financieros o gente con plata para pagar terminales Bloomberg a US$24.000 al año. **La economía es de todos** — la construimos todos con nuestro trabajo, la financiamos todos con nuestros impuestos, y sin embargo la mayoría de los chilenos no tiene acceso a herramientas decentes para entender dónde están parados.

Este proyecto nace de una convicción simple: **la información económica es un bien público y debe tratarse como tal.** Cuando la ciudadanía entiende la economía, toma mejores decisiones — al votar, al emprender, al organizarse. Una sociedad informada es una sociedad que no se deja pasar a llevar.

Los datos que muestra esta plataforma son **datos públicos del Banco Central de Chile**, recolectados a través de su API gratuita. No hay nada propietario acá. Lo único que hice fue tomar datos que ya son tuyos (porque los pagamos entre todos) y ponerlos en un formato visual, accesible y útil.

**Si Bloomberg puede cobrar US$24.000/año por un terminal financiero, Chile puede tener el suyo gratis.**

La idea es que esto genere un efecto de sinergia ciudadana: mientras más gente entienda la economía, mejores decisiones colectivas tomamos, y mejor nos va a todos. No es utopía — es sentido común.

---

## ¿Qué hace?

Bloomberg Chile es un dashboard económico completo con 5 pantallas de análisis:

### Tab 1: MERCADO
Vista general de todos los indicadores. Cotizaciones en tiempo real, gráficos interactivos, tablas con variaciones diarias, mensuales y trimestrales.

### Tab 2: ANALYTICS
- **Briefing económico** con insights generados algorítmicamente
- **Simulador de inversiones** — compara rendimiento histórico de UF, IPSA, USD/CLP y Depósito a Plazo
- **Matriz de correlaciones** entre indicadores económicos (Pearson pairwise)
- **Calendario económico** con eventos relevantes

### Tab 3: COBRE & FX
- Precio del cobre con medias móviles (SMA 20/50/200)
- Exportaciones mineras
- Comparativa de monedas latinoamericanas (CLP, BRL, ARS, COP, PEN, MXN) normalizada

### Tab 4: RENTA FIJA
- Curva de rendimiento (TPM, BCP 2Y, 5Y, 10Y) con detección de inversión
- Timeline de decisiones del Banco Central sobre la TPM
- Expectativas de operadores financieros (EOF)

### Tab 5: MACRO ANALYSIS
Análisis macroeconómico completo generado algorítmicamente:
- Score macro ponderado
- Detección de contradicciones entre indicadores
- Análisis de tendencias y momentum
- Síntesis narrativa con recomendaciones

---

## Indicadores disponibles (51 series)

### Tasas y Política Monetaria
| Indicador | Código BCCh | Frecuencia |
|-----------|-------------|------------|
| Tasa de Política Monetaria (TPM) | F022.TPM.TIN.D001.NO.Z.D | Diaria |
| Base Monetaria | F021.BMO.STO.N.CLP.0.M | Mensual |
| M1 (Agregado monetario) | F021.M1.STO.N.CLP.5.M | Mensual |
| M2 (Agregado monetario) | F021.M2.STO.N.CLP.5.M | Mensual |

### Tipo de Cambio
| Indicador | Código BCCh | Frecuencia |
|-----------|-------------|------------|
| USD/CLP | F073.TCO.PRE.Z.D | Diaria |
| EUR/CLP | F072.CLP.EUR.N.O.D | Diaria |
| CNY/CLP | F072.CLP.CNY.N.O.D | Diaria |
| BRL/CLP | F072.CLP.BRL.N.O.D | Diaria |
| ARS/CLP | F072.CLP.ARS.N.O.D | Diaria |
| COP/CLP | F072.CLP.COP.N.O.D | Diaria |
| PEN/CLP | F072.CLP.PEN.N.O.D | Diaria |
| MXN/CLP | F072.CLP.MXN.N.O.D | Diaria |
| Tipo de Cambio Real | F073.TCR.IND.199101.M | Mensual |

### Mercado y Precios
| Indicador | Código BCCh | Frecuencia |
|-----------|-------------|------------|
| IPSA (Bolsa de Santiago) | F013.IBC.IND.N.7.LAC.CL.CLP.BLO.D | Diaria |
| UF (Unidad de Fomento) | F073.UFF.PRE.Z.D | Diaria |
| Cobre (BML) | F019.PPB.PRE.100.D | Diaria |

### Bonos del Banco Central
| Indicador | Código BCCh | Frecuencia |
|-----------|-------------|------------|
| BCP 2 años | F022.BCLP.TIS.AN02.NO.Z.D | Diaria |
| BCP 5 años | F022.BCLP.TIS.AN05.NO.Z.D | Diaria |
| BCP 10 años | F022.BCLP.TIS.AN10.NO.Z.D | Diaria |

### Actividad e Inflación
| Indicador | Código BCCh | Frecuencia |
|-----------|-------------|------------|
| IMACEC | F032.IMC.IND.Z.Z.EP18.Z.Z.0.M | Mensual |
| IPC variación mensual | F074.IPC.VAR.Z.Z.C.M | Mensual |
| IPC variación anual | G073.IPC.V12.2023.M | Mensual |
| IPC Alimentos | F074.IPCA.VAR.Z.2023.C.M | Mensual |
| IPC Vivienda | F074.IPCVIV.VAR.Z.2023.C.M | Mensual |
| IPC Transables | F074.IPCT.VAR.Z.2023.C.M | Mensual |

### Empleo y Salarios
| Indicador | Código BCCh | Frecuencia |
|-----------|-------------|------------|
| Tasa de Desempleo | F049.DES.TAS.INE9.10.M | Mensual |
| Remuneraciones Nominales | F049.RMU.IND.HIST.81.M | Mensual |
| Remuneraciones Reales | G049.RMM.IND.INE23.R.M | Mensual |

### Confianza y Expectativas
| Indicador | Código BCCh | Frecuencia |
|-----------|-------------|------------|
| ICC (Confianza del Consumidor) | F089.ICC.IND.B1.M | Mensual |
| IPEC (Percepción Económica) | F089.IPE.IND.75M2.M | Mensual |
| IMCE (Confianza Empresarial) | G089.IME.IND.A0.M | Mensual |

### Comercio Exterior
| Indicador | Código BCCh | Frecuencia |
|-----------|-------------|------------|
| Exportaciones Totales | F068.B1.FLU.Z.0.C.N.Z.Z.Z.Z.6.0.M | Mensual |
| Importaciones Totales | F068.B1.FLU.Z.0.M.N.0.Z.Z.Z.6.0.M | Mensual |
| Balanza Comercial | F068.B1.VAR.T0.0.S.N.Z.Z.Z.Z.6.0.M | Mensual |
| Exportaciones Mineras | F068.B1.FLU.A1.0.C.N.Z.Z.Z.Z.6.0.M | Mensual |
| Exportaciones de Litio | F068.B1.FLU.A8.0.C.N.Z.Z.Z.Z.6.0.M | Mensual |
| Exportaciones de Cobre | F068.B1.FLU.A.0.C.N.Z.Z.Z.Z.6.0.M | Mensual |

### Sistema Financiero
| Indicador | Código BCCh | Frecuencia |
|-----------|-------------|------------|
| Colocaciones Bancarias | F022.CEF.STO.Z.Z.CLP.M | Mensual |
| Spread Bancario | F022.SBR.TIN.AN01.NO.Z.M | Mensual |
| Tasa de Captación | F022.CAP.TIN.AN01.NO.Z.M | Mensual |

### Sector Externo
| Indicador | Código BCCh | Frecuencia |
|-----------|-------------|------------|
| Reservas Internacionales | F062.A5.STO.PF.USD.M | Mensual |
| Cuenta Corriente | F068.A.FLU.Z.0.S.N.Z.Z.Z.Z.6.0.T | Trimestral |
| Deuda/PIB | F051.D7.PPB.C.Z.Z.T | Trimestral |
| Deuda Externa Corto Plazo | F068.T6.STO.Z.Z.S.P.Z.O.Z.Z.6.0.M | Mensual |
| Deuda Externa Largo Plazo | F068.T6.STO.Z.Z.S.P.Z.P.Z.Z.6.0.M | Mensual |

---

## ¿Cómo funcionan los datos?

### Pipeline de datos

```
Banco Central de Chile (si.api.bcch.cl)
         |
         | HTTPS (rate-limited: 3 req/seg)
         v
    bcch_client.py  ──→  raw_responses (JSON crudo, auditoría)
         |
         | Parseo mecánico (DD-MM-YYYY → ISO, string → float, NaN → NULL)
         v
    series_data (SQLite)  ──→  140,000+ observaciones
         |
         | Consultas SQL
         v
    routes.py (FastAPI)  ──→  JSON endpoints
         |
         | HTTP fetch
         v
    Frontend (Next.js/React)  ──→  Visualización
```

### Principios de integridad

1. **Raw First**: los datos se guardan tal cual vienen del API del BCCh. La tabla `raw_responses` almacena el JSON completo para auditoría.
2. **Solo parseo mecánico**: la única transformación es convertir fechas de DD-MM-YYYY a ISO y strings a números. **Nunca** se interpola, suaviza, redondea o modifica un valor.
3. **Derivados etiquetados**: cualquier cálculo nuestro (cambios porcentuales, correlaciones, promedios móviles) está claramente marcado como `derived: true` en la respuesta JSON.
4. **Transparencia total**: el StatusBar muestra en tiempo real cuándo fue la última actualización, cuántas series hay, y cuándo será el próximo refresh automático.

### Actualización automática

El backend tiene un scheduler que actualiza **todas las series cada 30 minutos** desde el API del Banco Central. También hay un botón de refresh manual en el frontend.

---

## Instalación

### Requisitos previos

- **Python 3.10+**
- **Node.js 18+**
- **Cuenta en el API del Banco Central de Chile** (gratis): https://si.api.bcch.cl/

### 1. Clonar el repositorio

```bash
git clone https://github.com/franciscoaldun/bloomberg-chile.git
cd bloomberg-chile
```

### 2. Configurar credenciales

```bash
cp .env.example .env
# Editar .env con tus credenciales del BCCh
```

El API del Banco Central es **gratuito**. Solo necesitai registrarte con tu email en https://si.api.bcch.cl/ y te dan usuario y contraseña.

### 3. Backend

```bash
cd backend
pip install -r requirements.txt
python main.py
```

El backend se levanta en `http://localhost:8000`. En el primer inicio, descarga automáticamente todas las series históricas del BCCh (puede tomar unos minutos).

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

El frontend se levanta en `http://localhost:3000`. Abrí esa URL en tu navegador.

### 5. Listo

El panel debería cargar con todos los datos. El backend se actualiza automáticamente cada 30 minutos.

---

## Navegación

| Tecla | Acción |
|-------|--------|
| `1` | Tab MERCADO |
| `2` | Tab ANALYTICS |
| `3` | Tab COBRE & FX |
| `4` | Tab RENTA FIJA |
| `5` | Tab MACRO ANALYSIS |
| `/` | Abrir línea de comandos |

### Comandos (presionar `/`)

- `refresh` — Actualizar datos manualmente
- Nombre de cualquier indicador para navegar directamente

---

## Arquitectura técnica

### Backend (Python/FastAPI)

```
backend/
├── main.py               # Servidor, scheduler de auto-refresh
├── routes.py             # Endpoints REST (/api/*)
├── config.py             # Catálogo de 51 series económicas
├── bcch_client.py        # Cliente HTTP para el API del BCCh
├── storage.py            # Capa SQLite (raw first)
├── analysis_engine.py    # Motor de análisis algorítmico
├── synthesis_engine.py   # Generador de síntesis macro
├── audit_verification.py # Verificación de integridad de datos
└── bloomberg_chile.db    # Base de datos SQLite (se genera sola)
```

### Frontend (Next.js/React/TypeScript)

```
frontend/src/
├── app/
│   └── page.tsx              # Terminal principal con 5 tabs
├── components/
│   ├── Mainboard1-5.tsx      # Layouts de cada tab
│   ├── PriceChart.tsx        # Gráficos interactivos (TradingView)
│   ├── CorrelationHeatmap.tsx # Matriz de correlaciones
│   ├── InvestmentSimulator.tsx # Simulador de inversiones
│   ├── MacroAnalysis.tsx     # Panel de análisis macro completo
│   ├── YieldCurveChart.tsx   # Curva de rendimiento
│   ├── StatusBar.tsx         # Barra de estado con refresh
│   └── ... (27 componentes en total)
├── hooks/
│   ├── useMarketData.ts      # Hook de datos con auto-refresh
│   └── useKeyboardNav.ts     # Navegación por teclado
├── lib/
│   ├── api.ts                # Cliente API
│   ├── format.ts             # Formateo de valores
│   └── commands.ts           # Parser de comandos
└── types/
    └── series.ts             # Definiciones TypeScript
```

### Endpoints principales

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/health` | GET | Estado del sistema y scheduler |
| `/api/dashboard` | GET | Todos los indicadores con último valor y cambio |
| `/api/series/{id}` | GET | Datos históricos de una serie |
| `/api/correlations` | GET | Matriz de correlación pairwise |
| `/api/simulator` | GET | Simulación de inversiones |
| `/api/cobre` | GET | Precio del cobre y exportaciones |
| `/api/fx/latam` | GET | Tipo de cambio LATAM normalizado |
| `/api/yield-curve` | GET | Curva de rendimiento |
| `/api/tpm-decisions` | GET | Historial de decisiones TPM |
| `/api/eof` | GET | Expectativas de operadores |
| `/api/macro-analysis` | GET | Análisis macro algorítmico |
| `/api/macro-synthesis` | GET | Síntesis narrativa |
| `/api/series/{id}/sma` | GET | Medias móviles |
| `/api/refresh` | POST | Trigger manual de actualización |

---

## Stack tecnológico

**Backend:**
- Python 3.10+ con FastAPI
- SQLite (modo WAL) para almacenamiento
- Correlación de Pearson calculada desde cero (sin numpy)
- Rate limiting para respetar el API del BCCh

**Frontend:**
- Next.js 16 + React 19 + TypeScript
- TailwindCSS 4 para estilos
- Lightweight Charts (TradingView) para gráficos
- IBM Plex (tipografía)

---

## Agradecimientos

Agradecimiento especial al **Banco Central de Chile** por mantener una API pública, gratuita y de calidad en https://si.api.bcch.cl/. Es un ejemplo de cómo las instituciones públicas pueden poner los datos al servicio de la ciudadanía. Ojalá más instituciones en Chile y Latinoamérica hicieran lo mismo.

---

## Autor

**Francisco Aldunate**

Estudiante de la Universidad de Talca. Creo que la tecnología tiene que estar al servicio de las personas, no al revés. Este proyecto es mi forma de aportar: tomar datos que ya son públicos y hacerlos accesibles pa cualquiera que quiera entender la economía de su país.

---

## Licencia

**Copyright (c) 2026 Francisco Aldunate. Todos los derechos reservados.**

Este software se distribuye de forma **gratuita y abierta** bajo los siguientes términos:

- **USO LIBRE**: cualquier persona puede usar, copiar, modificar y distribuir este software sin costo alguno.
- **PROHIBICIÓN COMERCIAL**: está **estrictamente prohibido** vender este software, cobrar por su acceso, o utilizarlo como base para productos comerciales. Esto incluye suscripciones, paywalls, licencias de pago, y cualquier forma de monetización directa o indirecta.
- **ATRIBUCIÓN**: cualquier redistribución debe mantener este aviso de licencia y dar crédito al autor original.
- **MISMA LICENCIA**: las obras derivadas deben distribuirse bajo estos mismos términos.

**Este proyecto es de Chile para Chile (y para quien quiera usarlo).** Los datos económicos son un bien público. Las herramientas para entenderlos también deberían serlo.

Ver archivo [LICENSE](LICENSE) para el texto legal completo.
