document.addEventListener("DOMContentLoaded", () => {
    
    // 1. Lógica del Carrito (Animación de Agregar sin recargar página)
    const formularios = document.querySelectorAll('form');
    
    formularios.forEach(form => {
      const action = form.getAttribute('action');
      if (action && action.includes('/carrito/agregar')) {
        form.addEventListener('submit', async (e) => {
          e.preventDefault(); // Evita la recarga rara de la página
          
          const btn = form.querySelector('button[type="submit"]');
          const textoOriginal = btn.innerHTML;
          
          btn.innerHTML = 'Agregando...';
          btn.classList.add('btn-agregando');
          
          try {
            const formData = new FormData(form);
            await fetch(action, {
              method: 'POST',
              body: formData
            });
            
            btn.innerHTML = 'Agregado';
            btn.classList.remove('btn-agregando');
            btn.classList.add('btn-agregado-exito');
            
            // Globo de Notificación
            const globo = document.createElement('div');
            globo.innerHTML = '🛒 Agregado al carrito';
            globo.className = 'globo-notificacion';
            document.body.appendChild(globo);
            
            requestAnimationFrame(() => {
              globo.classList.add('mostrar');
            });
            
            setTimeout(() => {
              btn.innerHTML = textoOriginal;
              btn.classList.remove('btn-agregado-exito');
              globo.classList.remove('mostrar');
              setTimeout(() => globo.remove(), 400);
            }, 2500);
            
          } catch (err) {
            console.error(err);
            btn.innerHTML = 'Error';
          }
        });
      }
    });

    // 2. Lógica del Panel Admin (Actualización de Stock Silenciosa)
    const stockForms = document.querySelectorAll('.stock-form');
    
    stockForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const btn = form.querySelector('.btn-stock');
            const originalText = btn.innerText;
            const originalBg = btn.style.backgroundColor;
            
            btn.innerText = "Guardando...";
            
            const formData = new FormData(form);
            
            fetch(form.action, {
                method: 'POST',
                body: formData
            }).then(() => {
                btn.innerText = "Actualizado";
                btn.style.backgroundColor = "var(--color-exito, #28a745)";
                btn.style.color = "white";
                
                const tr = form.closest('tr');
                const badge = tr.querySelector('.stock-badge');
                const nuevoStock = parseInt(formData.get('stock'));
                
                if (badge) {
                    badge.innerText = nuevoStock;
                    badge.className = "stock-badge";
                    tr.className = "admin-row";
                    
                    if (nuevoStock === 0) {
                        badge.classList.add("badge-agotado");
                        tr.classList.add("stock-agotado");
                    } else if (nuevoStock <= 3) {
                        badge.classList.add("badge-bajo");
                        tr.classList.add("stock-bajo");
                    } else {
                        badge.classList.add("badge-ok");
                    }
                }

                setTimeout(() => {
                    btn.innerText = originalText;
                    btn.style.backgroundColor = originalBg;
                }, 1500);
                
            }).catch(err => {
                console.error("Error conectando con la BD:", err);
                btn.innerText = "Error";
            });
        });
    });

});
