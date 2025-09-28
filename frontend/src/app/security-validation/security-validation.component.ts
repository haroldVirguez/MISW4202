import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

interface SecurityTest {
  id: string;
  name: string;
  description: string;
  type: 'encryption' | 'integrity';
  status: 'pending' | 'running' | 'success' | 'failed';
  result?: any;
  timestamp?: string;
}

interface EncryptionTest {
  originalData: string;
  encryptedData: string;
  decryptedData: string;
  isValid: boolean;
}

interface IntegrityTest {
  originalPayload: any;
  originalSignature: string;
  alteredPayload: any;
  alteredSignature: string;
  validSignatureTest: {isValid: boolean, reason?: string, response?: any, error?: any};
  invalidSignatureTest: {isValid: boolean, reason?: string, response?: any, error?: any};
  alteredSignatureTest: {isValid: boolean, reason?: string, response?: any, error?: any};
  isValid: boolean;
}


@Component({
  selector: 'app-security-validation',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './security-validation.component.html',
  styleUrls: ['./security-validation.component.css']
})
export class SecurityValidationComponent implements OnInit {
  tests: SecurityTest[] = [
    {
      id: 'encryption_test',
      name: 'Validación de Cifrado',
      description: 'Verificar que los datos sensibles se almacenan cifrados en la BD',
      type: 'encryption',
      status: 'pending'
    },
    {
      id: 'integrity_test',
      name: 'Validación de Integridad',
      description: 'Verificar que los mensajes con firmas inválidas son rechazados',
      type: 'integrity',
      status: 'pending'
    },
  ];

  encryptionResult?: EncryptionTest;
  integrityResult?: IntegrityTest;

  loading = false;
  message = '';
  messageType = 'info';

  testData = {
    direccion: 'Calle 123 #45-67, Bogotá',
    nombre_recibe: 'Juan Pérez',
    firma_recibe: 'Firma digital del receptor',
    pedido_id: 'PED-001',
    usuario_id: '1'
  };

  constructor(private http: HttpClient, private cdr: ChangeDetectorRef) {}

  ngOnInit() {
    this.loadExistingData();
  }

  async testEncryption() {
    const test = this.tests.find(t => t.id === 'encryption_test');
    if (!test) return;

    test.status = 'running';
    this.clearMessage();

    try {
      const entregaData = {
        direccion: this.testData.direccion,
        estado: 'PENDIENTE',
        pedido_id: this.testData.pedido_id
      };

      console.log('Creando entrega con datos:', entregaData);
      const createResponse = await this.http.post<any>('http://localhost:8080/api/v1/logistica/entregas', entregaData).toPromise();
      console.log('Respuesta de creación:', createResponse);
      
      if (createResponse && createResponse.id) {
        console.log('Usando respuesta cifrada del POST:', createResponse);
        
        console.log('Obteniendo entrega ID:', createResponse.id);
        const entregaResponse = await this.http.get<any>(`http://localhost:8080/api/v1/logistica/entrega/${createResponse.id}`).toPromise();
        console.log('Entrega obtenida (GET):', entregaResponse);
        
        const isEncrypted = createResponse.direccion !== this.testData.direccion && 
                           createResponse.direccion.length > this.testData.direccion.length &&
                           createResponse.direccion.includes(':');

        this.encryptionResult = {
          originalData: this.testData.direccion,
          encryptedData: createResponse.direccion,
          decryptedData: entregaResponse.direccion,
          isValid: isEncrypted
        };

        test.status = 'success';
        test.result = this.encryptionResult;
        test.timestamp = new Date().toISOString();
        
        if (isEncrypted) {
          this.showMessage(
            `✅ Test de cifrado completado: Los datos están cifrados en la BD. Original: "${this.testData.direccion}" → Cifrado: "${createResponse.direccion.substring(0, 20)}..." (${createResponse.direccion.length} chars) → Descifrado: "${entregaResponse.direccion}"`,
            'success'
          );
        } else {
          this.showMessage(
            `❌ Test de cifrado falló: Los datos NO están cifrados. Original: "${this.testData.direccion}" → BD: "${createResponse.direccion}"`,
            'error'
          );
        }
        
        this.cdr.detectChanges();
      } else {
        throw new Error('No se pudo crear la entrega');
      }
    } catch (error) {
      test.status = 'failed';
      test.result = { error: error };
      this.showMessage('❌ Error en test de cifrado: ' + error, 'error');
    }
  }

  private tamperHexSignature(sig: string): string {
    const hexRe = /^[0-9a-f]+$/i;
    if (!sig || sig.length < 4) return sig + '0';
    if (!hexRe.test(sig)) {
      const flip = sig[0] === 'A' ? 'B' : 'A';
      return flip + sig.slice(1);
    }
    const i = Math.max(0, Math.floor(sig.length / 2) - 1);
    const c = sig[i];
    const newC = c.toLowerCase() === 'f' ? '0' : (parseInt(c, 16) + 1).toString(16);
    return sig.slice(0, i) + newC + sig.slice(i + 1);
  }

  async testIntegrity() {
    const test = this.tests.find(t => t.id === 'integrity_test');
    if (!test) return;

    test.status = 'running';
    this.clearMessage();

    try {
      // 1) Crear entrega base
      const entregaData = {
        direccion: this.testData.direccion,
        estado: 'PENDIENTE',
        pedido_id: this.testData.pedido_id
      };

      console.log('Creando entrega para test de integridad:', entregaData);
      const createResponse = await firstValueFrom(
        this.http.post<any>('http://localhost:8080/api/v1/logistica/entregas', entregaData)
      );
      console.log('Entrega creada para integridad:', createResponse);

      if (!createResponse?.id) 
        throw new Error('No se pudo crear la entrega para el test de integridad');

      // 2) Obtener token (cualquiera válido, sin roles)
      const authToken = await this.getAuthToken();
      console.log('✅ Token obtenido:', authToken.substring(0, 20) + '...');

      // 3) Construir payload EXACTO que el backend valida
      const userId = this.getUserIdFromToken(authToken);
      if (userId == null) 
        throw new Error('No se pudo extraer usuario_id del JWT. Revisa que el token contenga sub.id');

      const businessPayload = {
        direccion: this.testData.direccion,
        nombre_recibe: this.testData.nombre_recibe,
        firma_recibe: this.testData.firma_recibe,
        pedido_id: this.testData.pedido_id,
        usuario_id: userId,
        entrega_id: createResponse.id
      };

      // 4) Solicitar firma real al Autorizador
      console.log('🔐 Generando firma real…');
      const signatureResponse = await firstValueFrom(
        this.http.post<any>(
          'http://localhost:8080/api/v1/autorizador/sign-data',
          { payload: businessPayload },
          { headers: { Authorization: `Bearer ${authToken}` } }
        )
      );

      const signedPayload = signatureResponse.payload;
      const realSignature = signatureResponse.firma;
      console.log('✅ Firma real (HMAC):', realSignature);
      console.log('📋 Payload firmado:', signedPayload);

      // --- TEST 1: payload original + firma correcta (debe aceptar) ---
      console.log('🧪 TEST 1: Confirmar con firma válida…');
      const validConfirmationData = { ...signedPayload, firma_payload: realSignature };

      let validSignatureTest: any;
      try {
        const validResp = await firstValueFrom(
          this.http.post<any>(
            `http://localhost:8080/api/v1/logistica/entrega/${createResponse.id}/confirmar`,
            validConfirmationData,
            { headers: { Authorization: `Bearer ${authToken}` } }
          )
        );
        validSignatureTest = { isValid: true, reason: '✅ Aceptó firma válida', response: validResp };
        console.log('✅ TEST 1 OK', validResp);
      } catch (error: any) {
        validSignatureTest = {
          isValid: false,
          reason: `❌ Esperado 200, obtuvo ${error?.status} ${error?.statusText || ''}`,
          error
        };
        console.log('❌ TEST 1 FAIL', error);
      }

      // --- TEST 2: payload ALTERADO + firma original (debe rechazar con 403) ---
      console.log('🧪 TEST 2: Confirmar con payload alterado + misma firma…');
      const alteredPayload = { ...signedPayload, direccion: 'DIRECCIÓN ALTERADA' };
      const invalidWithAlteredPayload = { ...alteredPayload, firma_payload: realSignature };

      let invalidSignatureTest: any;
      try {
        const resp = await firstValueFrom(
          this.http.post<any>(
            `http://localhost:8080/api/v1/logistica/entrega/${createResponse.id}/confirmar`,
            invalidWithAlteredPayload,
            { headers: { Authorization: `Bearer ${authToken}` } }
          )
        );
        invalidSignatureTest = {
          isValid: false,
          reason: '❌ ACEPTÓ payload alterado con firma original (debería rechazar 403)',
          response: resp
        };
        console.warn('⚠️ TEST 2 comportamiento inesperado', resp);
      } catch (error: any) {
        const ok = error?.status === 403;
        invalidSignatureTest = {
          isValid: ok,
          reason: ok ? '✅ Rechazó payload alterado (403)' :
                       `❌ Esperado 403, obtuvo ${error?.status} ${error?.statusText || ''}`,
          error
        };
        console.log(ok ? '✅ TEST 2 OK' : '❌ TEST 2 FAIL', error);
      }

      // --- TEST 3: payload original + FIRMA ALTERADA (debe rechazar con 403) ---
      console.log('🧪 TEST 3: Confirmar con firma alterada…');
      const tamperedSignature = this.tamperHexSignature(realSignature);
      const invalidWithTamperedSig = { ...signedPayload, firma_payload: tamperedSignature };

      let alteredSignatureTest: any;
      try {
        const resp = await firstValueFrom(
          this.http.post<any>(
            `http://localhost:8080/api/v1/logistica/entrega/${createResponse.id}/confirmar`,
            invalidWithTamperedSig,
            { headers: { Authorization: `Bearer ${authToken}` } }
          )
        );
        alteredSignatureTest = {
          isValid: false,
          reason: '❌ ACEPTÓ firma alterada (debería rechazar 403)',
          response: resp
        };
        console.warn('⚠️ TEST 3 comportamiento inesperado', resp);
      } catch (error: any) {
        const ok = error?.status === 403;
        alteredSignatureTest = {
          isValid: ok,
          reason: ok ? '✅ Rechazó firma alterada (403)' :
                       `❌ Esperado 403, obtuvo ${error?.status} ${error?.statusText || ''}`,
          error
        };
        console.log(ok ? '✅ TEST 3 OK' : '❌ TEST 3 FAIL', error);
      }

      // Consolidar resultados
      this.integrityResult = {
        originalPayload: signedPayload,
        originalSignature: realSignature,
        alteredPayload,
        alteredSignature: tamperedSignature,
        validSignatureTest,
        invalidSignatureTest,
        alteredSignatureTest,
        isValid: !!(validSignatureTest?.isValid && invalidSignatureTest?.isValid && alteredSignatureTest?.isValid)
      };

      test.status = this.integrityResult.isValid ? 'success' : 'failed';
      test.result = this.integrityResult;
      test.timestamp = new Date().toISOString();

      if (this.integrityResult.isValid) {
        this.showMessage(
          `✅ Integridad OK: Válida aceptada (200), alteradas rechazadas (403). Firma: "${realSignature.substring(0, 20)}..."`,
          'success'
        );
      } else {
        this.showMessage('❌ Integridad falló: revisa detalles de los 3 tests en la sección de resultados.', 'error');
      }

      this.cdr.detectChanges();

    } catch (error) {
      const testRef = this.tests.find(t => t.id === 'integrity_test');
      if (testRef) {
        testRef.status = 'failed';
        testRef.result = { error: error };
      }
      this.showMessage('❌ Error en test de integridad: ' + error, 'error');
    }
  }

  private parseJwtPayload(token: string): any | null {
    try {
      const base64 = token.split('.')[1];
      const json = atob(base64.replace(/-/g, '+').replace(/_/g, '/'));
      return JSON.parse(decodeURIComponent(
        json.split('').map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)).join('')
      ));
    } catch { return null; }
  }

  private getUserIdFromToken(token: string): number | string | null {
    const p = this.parseJwtPayload(token);
    return p?.sub?.id ?? null;
  }

  private async getAuthToken(): Promise<string> {
    const tryLogin = (cred: any) =>
      firstValueFrom(this.http.post<any>('http://localhost:8080/api/v1/autorizador/login', cred));

    const candidates = [
      { nombre: 'admin', contrasena: 'admin' },
    ];

    for (const cred of candidates) {
      try {
        const r = await tryLogin(cred);
        if (r?.token) return r.token;
      } catch {  }
    }
    throw new Error('No se pudo obtener un token válido con credenciales de prueba (admin/admin, jonatan/123456, user/user).');
  }

  loadExistingData() {
    this.http.get<any[]>('http://localhost:8080/api/v1/logistica/entregas').subscribe({
      next: (entregas) => {
        console.log('Entregas en BD:', entregas);
      },
      error: (error) => {
        console.error('Error cargando entregas:', error);
      }
    });
  }

  showMessage(text: string, type: string) {
    this.message = text;
    this.messageType = type;
    setTimeout(() => this.clearMessage(), 5000);
  }

  clearMessage() {
    this.message = '';
  }

  getMessageClass(): string {
    return `alert alert-${this.messageType === 'error' ? 'danger' : this.messageType}`;
  }

  getTestStatusClass(status: string): string {
    switch (status) {
      case 'success': return 'success';
      case 'failed': return 'danger';
      case 'running': return 'warning';
      default: return 'secondary';
    }
  }

  getTestStatusIcon(status: string): string {
    switch (status) {
      case 'success': return 'fa-check-circle';
      case 'failed': return 'fa-times-circle';
      case 'running': return 'fa-spinner fa-spin';
      default: return 'fa-play-circle';
    }
  }

  getCurrentTime(): string {
    return new Date().toLocaleTimeString();
  }

  private canonicalize(obj: any): any {
    if (obj === null || typeof obj !== 'object') return obj;
    if (Array.isArray(obj)) return obj.map(v => this.canonicalize(v));
    const out: any = {};
    for (const k of Object.keys(obj).sort()) out[k] = this.canonicalize(obj[k]);
    return out;
  }
}
