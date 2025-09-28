import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

interface User {
  id: number;
  nombre: string;
  roles: string;
}

interface LoginResponse {
  mensaje: string;
  token: string;
}

interface SignupResponse {
  mensaje: string;
  usuario: User;
}

interface SignatureResponse {
  payload: any;
  firma: string;
  timestamp: string;
}

interface ValidationResponse {
  payload: any;
  firma: string;
  timestamp: string;
  firma_valida: boolean;
}

@Component({
  selector: 'app-auth',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './auth.component.html',
  styleUrls: ['./auth.component.css']
})
export class AuthComponent implements OnInit {
  isLoggedIn = false;
  currentUser: User | null = null;
  authToken: string | null = null;
  
  loginForm = {
    nombre: '',
    contrasena: ''
  };
  
  signupForm = {
    nombre: '',
    contrasena: '',
    roles: 'user'
  };
  
  showLogin = true;
  showSignup = false;
  showSignature = false;
  showValidation = false;
  loginLoading = false;
  signupLoading = false;
  signatureLoading = false;
  validationLoading = false;
  
  signatureData = {
    payload: '',
    firma: '',
    timestamp: ''
  };
  
  validationData = {
    payload: '',
    firma: '',
    resultado: null as ValidationResponse | null
  };
  
  message = '';
  messageType = 'info';

  constructor(private http: HttpClient, private cdr: ChangeDetectorRef) {}

  ngOnInit() {
    this.checkAuthStatus();
  }

  checkAuthStatus() {
    const token = localStorage.getItem('auth_token');
    if (token) {
      this.authToken = token;
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        this.currentUser = {
          id: payload.sub.id,
          nombre: payload.sub.nombre,
          roles: payload.sub.roles
        };
        this.isLoggedIn = true;
      } catch (error) {
        localStorage.removeItem('auth_token');
        this.authToken = '';
        this.isLoggedIn = false;
        this.currentUser = null;
      }
    } else {
      this.isLoggedIn = false;
      this.currentUser = null;
    }
  }

  toggleView(view: string) {
    this.showLogin = view === 'login';
    this.showSignup = view === 'signup';
    this.showSignature = view === 'signature';
    this.showValidation = view === 'validation';
    this.clearMessage();
  }

  login() {
    this.loginLoading = true;
    this.clearMessage();
    
    console.log('Enviando datos de login:', this.loginForm);
    
    this.http.post<LoginResponse>('http://localhost:8080/api/v1/autorizador/login', this.loginForm)
      .subscribe({
        next: (response) => {
          console.log('Respuesta del login:', response);
          this.authToken = response.token;
          this.isLoggedIn = true;
          localStorage.setItem('auth_token', response.token);
          
          try {
            const payload = JSON.parse(atob(response.token.split('.')[1]));
            this.currentUser = {
              id: payload.sub.id,
              nombre: payload.sub.nombre,
              roles: payload.sub.roles
            };
            console.log('Usuario actualizado:', this.currentUser);
          } catch (error) {
            console.error('Error decodificando token:', error);
          }
          
          this.showMessage('Inicio de sesión exitoso', 'success');
          this.loginLoading = false;
          this.loginForm = { nombre: '', contrasena: '' };
          this.cdr.detectChanges();
        },
        error: (error) => {
          console.error('Error en login:', error);
          this.showMessage('Error en el inicio de sesión: ' + (error.error?.mensaje || error.message), 'error');
          this.loginLoading = false;
          this.cdr.detectChanges();
        }
      });
  }

  signup() {
    this.signupLoading = true;
    this.clearMessage();
    
    console.log('Enviando datos de registro:', this.signupForm);
    
    this.http.post<SignupResponse>('http://localhost:8080/api/v1/autorizador/signup', this.signupForm)
      .subscribe({
        next: (response) => {
          console.log('Respuesta del servidor:', response);
          this.showMessage('Usuario creado exitosamente', 'success');
          this.signupForm = { nombre: '', contrasena: '', roles: 'user' };
          this.signupLoading = false;
          console.log('signupLoading reseteado a:', this.signupLoading);
          this.cdr.detectChanges();
          this.toggleView('login');
        },
        error: (error) => {
          console.error('Error en registro:', error);
          this.showMessage('Error creando usuario: ' + (error.error?.mensaje || error.message), 'error');
          this.signupLoading = false;
          console.log('signupLoading reseteado a:', this.signupLoading);
          this.cdr.detectChanges();
        }
      });
  }

  generateSignature() {
    this.signatureLoading = true;
    this.clearMessage();
    
    console.log('Generando firma con payload:', this.signatureData.payload);
    console.log('Token de autorización:', this.authToken);
    
    const payload = JSON.parse(this.signatureData.payload || '{}');
    
    this.http.post<SignatureResponse>('http://localhost:8080/api/v1/autorizador/sign-data', {
      payload: payload
    }, {
      headers: {
        'Authorization': `Bearer ${this.authToken}`
      }
    })
    .subscribe({
      next: (response) => {
        console.log('Respuesta de firma:', response);
        this.signatureData.firma = response.firma;
        this.signatureData.timestamp = response.timestamp;
        this.showMessage('Firma generada exitosamente', 'success');
        this.signatureLoading = false;
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('Error generando firma:', error);
        this.showMessage('Error generando firma: ' + (error.error?.mensaje || error.message), 'error');
        this.signatureLoading = false;
        this.cdr.detectChanges();
      }
    });
  }

  validateSignature() {
    this.validationLoading = true;
    this.clearMessage();
    
    const payload = JSON.parse(this.validationData.payload || '{}');
    
    this.http.post<ValidationResponse>('http://localhost:8080/api/v1/autorizador/validate-signature', {
      payload: payload,
      firma: this.validationData.firma
    })
    .subscribe({
      next: (response) => {
        this.validationData.resultado = response;
        this.showMessage(
          response.firma_valida ? 'Firma válida' : 'Firma inválida', 
          response.firma_valida ? 'success' : 'error'
        );
        this.validationLoading = false;
      },
      error: (error) => {
        this.showMessage('Error validando firma: ' + (error.error?.mensaje || error.message), 'error');
        this.validationLoading = false;
      }
    });
  }

  logout() {
    this.authToken = null;
    this.isLoggedIn = false;
    this.currentUser = null;
    localStorage.removeItem('auth_token');
    this.showMessage('Sesión cerrada', 'info');
    this.toggleView('login');
  }

  showMessage(text: string, type: string) {
    this.message = text;
    this.messageType = type;
  }

  clearMessage() {
    this.message = '';
  }

  getMessageClass(): string {
    return `alert alert-${this.messageType === 'error' ? 'danger' : this.messageType}`;
  }
}
