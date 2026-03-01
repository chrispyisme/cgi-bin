# ===== USAGE EXAMPLE =====

if __name__ == "__main__":
    from lib.di.Container import Container
    
    # Create your container
    c = Container()
    
    # Wrap it with ServiceManager
    sm = ServiceManager(c)
    
    print("=" * 70)
    print("ServiceManager with YOUR Container")
    print("=" * 70)
    
    # Add services
    sm.add('lib.http.Request.Request', 'lib.http.Request.Request', 'singleton')
    
    sm.add('router', 'lib.routing.Router.Router', 'singleton',
           params={'request': 'lib.http.Request.Request'},  # Auto-resolves!
           tags=['routing', 'http'])
    
    sm.add('database', 'lib.db.Database.Database', 'singleton',
           params={'host': 'localhost', 'port': 5432},
           tags=['database', 'core'])
    
    # Or bulk load
    services = [
        {
            "abstract": "cache",
            "concrete": "lib.cache.Cache.Cache",
            "type": "singleton",
            "params": {"driver": "redis"},
            "tags": ["cache"]
        }
    ]
    sm.load_services(services)
    
    # Query
    print("\nAll services:", sm.list_services())
    print("Singletons:", sm.get_singletons())
    print("Tagged 'core':", sm.get_tagged('core'))
    
    # Update
    sm.update('database', params={'host': 'prod.db.com'})
    print("\n✓ Updated database")
    
    # Remove
    sm.remove('cache')
    print("✓ Removed cache")
    
    # Print registry
    sm.print_registry()
    
    # Use the container through ServiceManager
    # router = sm.make('router')