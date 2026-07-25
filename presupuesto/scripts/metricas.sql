-- Métricas de uso del sistema de Presupuesto.
-- Uso: psql -h <HOST> -U <USUARIO> -d presupuestodb -f presupuesto/scripts/metricas.sql
SELECT
    COUNT(DISTINCT colaborador_id)               AS usuarios_que_usaron_la_app,
    COUNT(*)                                      AS solicitudes_creadas_total,
    COUNT(*) FILTER (WHERE estado = 'PENDIENTE')  AS pendientes,
    COUNT(*) FILTER (WHERE estado = 'POR_REVISION') AS por_revision,
    COUNT(*) FILTER (WHERE estado = 'APROBADA')   AS presupuestos_aprobados,
    COUNT(*) FILTER (WHERE estado = 'RECHAZADA')  AS rechazadas
FROM presupuesto_solicitudpresupuesto;
