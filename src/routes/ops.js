import { readJson } from '../lib/http.js';
import * as ops from '../core/ops.js';

export function registerOpsRoutes(router) {
  router.get('/api/ops/overview', () => ops.overview());

  router.get('/api/ops/vehicles', ({ query }) =>
    ops.listVehicles({
      status: query.get('status') || undefined,
      branch: query.get('branch') || undefined,
      q: query.get('q') || undefined,
    }),
  );

  router.get('/api/ops/contracts', ({ query }) =>
    ops.listContracts({
      status: query.get('status') || undefined,
      date: query.get('date') || undefined,
      q: query.get('q') || undefined,
    }),
  );

  router.get('/api/ops/contracts/:id', ({ params }) => ops.getContract(params.id));

  router.get('/api/ops/bookings', ({ query }) =>
    ops.listBookings({
      date: query.get('date') || undefined,
      status: query.get('status') || undefined,
    }),
  );

  router.get('/api/ops/tasks', ({ query }) =>
    ops.listTasks({
      date: query.get('date') || undefined,
      type: query.get('type') || undefined,
    }),
  );

  router.get('/api/ops/customers', ({ query }) => ops.searchCustomers(query.get('q') || ''));

  router.get('/api/ops/customer-context', ({ query }) =>
    ops.customerContext(query.get('phone') || ''),
  );

  // ===== أوامر =====

  router.post('/api/ops/contracts/:id/extend', async ({ params, req, actor }) => {
    const body = await readJson(req);
    return ops.extendContract(params.id, Number(body.days), actor);
  });

  router.post('/api/ops/contracts/:id/close', async ({ params, req, actor }) => {
    const body = await readJson(req);
    return ops.closeContract(params.id, { odometer: body.odometer, notes: body.notes }, actor);
  });

  router.post('/api/ops/vehicles/:id/status', async ({ params, req, actor }) => {
    const body = await readJson(req);
    return ops.setVehicleStatus(params.id, body.status, body.note, actor);
  });

  router.post('/api/ops/tasks/:id/assign', async ({ params, req, actor }) => {
    const body = await readJson(req);
    return ops.assignTask(params.id, body.driver, actor);
  });

  router.post('/api/ops/tasks/:id/complete', async ({ params, req, actor }) => {
    const body = await readJson(req);
    return ops.completeTask(params.id, body.note, actor);
  });

  router.post('/api/ops/notes', async ({ req, actor }) => {
    const body = await readJson(req);
    return ops.addNote({
      refType: body.refType,
      refId: body.refId,
      body: body.body,
      author: actor,
    });
  });
}
