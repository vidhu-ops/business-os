# iidatech.com DNS (name.com) -> Render business-os-2

Add these records at name.com for iidatech.com:

ANAME/ALIAS  @    -> business-os-2.onrender.com
CNAME        www  -> business-os-2.onrender.com

Render: Custom Domains -> iidatech.com Verified
Env: PUBLIC_APP_URL=https://iidatech.com

Without apex A/ANAME/CNAME, the domain will not load.
