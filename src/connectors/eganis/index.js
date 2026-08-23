import { config } from '../../config.js';
import { log } from '../../lib/log.js';
import { createMockDriver } from './mock.js';
import { createApiDriver } from './api.js';
import { createBrowserDriver } from './browser.js';
import { createHttpDriver } from './http.js';

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
  // «browser» يبقى مفهوماً لمن ضبطه سابقاً، لكنه يعني الآن القراءة الخفيفة:
  // Chromium لا يسع الخطط الصغيرة فيُسقط التطبيق كلّه، والصفحات HTML عادي.
  else if (driver === 'http' || driver === 'browser') instance = createHttpDriver();
  else if (driver === 'browser-full') instance = createBrowserDriver();
  else instance = createMockDriver();
  log.info(`eganis: تم تفعيل السائق "${instance.name}"`);
  return instance;
}

/** لإعادة التهيئة بعد تغيير الإعدادات (يُستخدم في الاختبارات) */
export function resetEganis() {
  instance = null;
}
