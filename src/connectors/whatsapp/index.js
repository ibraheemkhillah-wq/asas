import { config } from '../../config.js';
import { log } from '../../lib/log.js';
import { createMockWhatsappDriver } from './mock.js';
import { createCloudDriver } from './cloud.js';

let instance = null;

export function whatsapp() {
  if (instance) return instance;
  instance = config.whatsapp.driver === 'cloud' ? createCloudDriver() : createMockWhatsappDriver();
  log.info(`whatsapp: تم تفعيل السائق "${instance.name}"`);
  return instance;
}

export function resetWhatsapp() {
  instance = null;
}
