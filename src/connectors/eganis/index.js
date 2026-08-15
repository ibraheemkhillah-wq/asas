import { config } from '../../config.js';
import { log } from '../../lib/log.js';
import { createMockDriver } from './mock.js';
import { createApiDriver } from './api.js';
import { createBrowserDriver } from './browser.js';

let instance = null;

/**
 * الواجهة الموحّدة لـ eganis. كل السوّاق (mock / api / browser) تطبّق نفس التوقيعات:
 *   health, listVehicles, listContracts, getContract, listBookings, listTasks,
 *   searchCustomers, findCustomerByPhone, extendContract, closeContract,
 *   setVehicleStatus, assignTask, completeTask, snapshot
 */
export function eganis() {
  if (instance) return instance;
  const driver = config.eganis.driver;
  if (driver === 'api') instance = createApiDriver();
  else if (driver === 'browser') instance = createBrowserDriver();
  else instance = createMockDriver();
  log.info(`eganis: تم تفعيل السائق "${instance.name}"`);
  return instance;
}

/** لإعادة التهيئة بعد تغيير الإعدادات (يُستخدم في الاختبارات) */
export function resetEganis() {
  instance = null;
}
