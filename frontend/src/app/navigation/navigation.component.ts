import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, NavigationEnd } from '@angular/router';
import { filter } from 'rxjs/operators';

@Component({
  selector: 'app-navigation',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './navigation.component.html',
  styleUrls: ['./navigation.component.css']
})
export class NavigationComponent implements OnInit {
  currentRoute = '';
  isMenuOpen = false;

  menuItems = [
    {
      path: '/monitor',
      title: 'Monitor',
      icon: 'fas fa-heartbeat',
      description: 'Monitoreo del sistema'
    },
    {
      path: '/auth',
      title: 'Autenticación',
      icon: 'fas fa-shield-alt',
      description: 'Gestión de usuarios y firmas'
    },
    {
      path: '/security-validation',
      title: 'Validación de Seguridad',
      icon: 'fas fa-shield-alt',
      description: 'Experimentos de seguridad interactivos'
    }
  ];

  constructor(private router: Router) {}

  ngOnInit() {
    this.router.events
      .pipe(filter(event => event instanceof NavigationEnd))
      .subscribe((event: NavigationEnd) => {
        this.currentRoute = event.url;
      });
  }

  navigateTo(path: string) {
    this.router.navigate([path]);
    this.isMenuOpen = false;
  }

  toggleMenu() {
    this.isMenuOpen = !this.isMenuOpen;
  }

  isActive(path: string): boolean {
    return this.currentRoute === path;
  }
}
