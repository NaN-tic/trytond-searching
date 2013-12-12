==============================
Búsqueda avanzada con perfiles
==============================

El módulo de búsqueda avanzada le permite la búsqueda de registros en cualquier modelo
del ERP.

Las búsquedas por defecto de Tryton le permiten búsquedas básicas. Dispone de un sistema
gráfico para la realización de búsquedas (con el botón Filtro) o usted mismo puede ir
escribiendo el filtro a usar. Asi mismo, los filtros que cree los puede ir guardando 
como preferidos. Es un sistema de búsqueda potente pero también limitado, ya que sólo le
permite buscar en los campos que se encuentran en la vista de listado. Si desea buscar por
campos que no se encuentren en esta vista no podrá buscar por estos.

También dispone de un asistente más complejo tanto para el usuario como las búsquedas mediante
perfiles de filtros - condiciones del perfil. Este módulo es una herramienta
de búsqueda entremedio de las búsquedas por defecto y Babi (Basic Business Intelligence).

--------
Perfiles
--------

Los perfiles son la agrupación de condiciones que se usaran para la búsqueda. También un
perfil va relacionado a un modelo; el modelo es el objeto en que se quiere buscar. Por ejemplo,
si deseamos buscar en terceros, el modelo será "party".

Los perfiles los puede editar desde el menú |menu_searching_profile_form|.

Los perfiles los podemos relacionar con grupos de usuarios. Al añadir un grupo al perfil,
ese perfil sólo estará visible/disponible para ese grupo. Por ejemplo, si crea un perfil
para ventas, añade que esté disponible para los usuarios de "ventas".

La edición de grupos en los perfiles sólo lo podrán hacer los usuarios que sean del
grupo "Administrador".

-----------
Condiciones
-----------

Según los perfiles, dispondremos de unos campos o otros dependiendo a que modelo va relacionado.

Las condiciones nos permiten:

* secuencia: el orden de las condiciones
* campo: el campo del modelo que se usará para la condición.
* operador: el operador "matemático" para buscar.
* valor: el resultado que debemos encontrar.
* condición: AND o OR

AND - OR
--------

Con AND y OR le permite hacer condiciones que los resultados concidan con la condición
o esten disponibles.

La versión actual de la búsqueda avanzada permite este tipo de condiciones AND-OR, pero
tienen un límite: todas las condiciones OR se agrupan en el primer bloque y las AND en 
un segundo bloque. Para condiciones más complejas use el sistema de dominios de Python
del perfil.

En el apartado de ejemplos puede ver una condición de este tipo.

Dominios
--------

Si se requieren búsquedas complejas, puede usar el sistema de dominios de Python dónde
podrá escribir una condición. Consulte el apartado "domain" de http://doc.tryton.org para
documentación técnica sobre los dominos.

Ejemplos de condiciones
-----------------------

* Ejemplo de perfil de terceros que se llamen "zikzakmedia" y que estén en la
categoría de "Mantenimiento".

.. code-block:: csv

    "0","name","ilike","zikzakmedia%"
    "0","categories","=","Mantenimiento"

En este ejemplo usamos el operador "ilike" y usamos el comodin "%" para buscar todos
los nombres de terceros que empiezen por "zikzakmedia".

* Ejemplo de perfil de terceros que se llamen "zikzakmedia" y que la calle sea "Dr. Fleming".

.. code-block:: csv

    "0","name","","ilike","Zikzakmedia%"
    "0","addresses","street","ilike","Dr. Fleming%"

En este ejemplo es similar al anterior pero la diferencia es que a parte de terceros estamos
buscando también en las direcciones de terceros. En este caso debemos añadir cual es el campo
que relaciona tercero con la dirección (addresses). Y para la condición, usaremos el subcampo
(street).

Sólo los campos relacionados (one2many - un cliente tiene varias direcciones) estará disponible
el campo subcampo. Si no, este campo no lo podrá editar.

* Ejemplo de perfil de terceros que se llamen "zikzakmedia" y que el código postal sea "08720".

.. code-block:: csv

    "0","name","ilike","Zikzakmedia%"
    "0","zip","=","O8720"

En este ejemplo es muy similar al anterior, pero no hemos usado un subcampo para la relación. En
este caso no hace falta ya que interamente las direcciones, a parte de buscar por el nombre de la
dirección, también se busca por ciudad y código postal. En este ejemplo es algo diferente y no
común.

* Ejemplo con condiciones con AND - OR:

.. code-block:: csv

    "0","addresses","zip","=","08770","OR"
    "1","addresses","zip","=","08720","OR"
    "3","addresses","zip","=","08000","OR"
    "4","name","","ilike","Zikzakmedia%","AND"

En este ejemplo buscaremos todos los terceros con los códigos postales "08770, 08720 y 08000" y que
el nombre del tercero empieze por "zikzakmedia".

--------
Búsqueda
--------

Disponemos de un asistente para seleccionar el perfil con las condiciones a buscar.
Cuando accionamos el asistente con el perfil, nos abrirá una nueva pestaña del objeto
relacionado con las condiciones del perfil. Para la ejecución de búsquedas mediante
perfiles accione el menú |menu_act_searching|.

Si desea cambiar las condiciones, edite el perfil con las nuevas opciones. La edición
se puede hacer desde el mismo asistente o mediante el menú |menu_searching_profile_form|.

-------
Modelos
-------

Para activar que modelos estan disponibles en las perfiles debe activar la opción |searching_enabled|
que encontrará en el modelo (sólo lo podrán activar los usuarios del grupo "Administración").


.. |searching_enabled| field:: ir.model/searching_enabled
.. |menu_act_searching| tryref:: searching.menu_act_searching/complete_name
.. |menu_searching_profile_form| tryref:: searching.menu_searching_profile_form/complete_name
