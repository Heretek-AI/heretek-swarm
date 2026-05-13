# Secrets Manifest

**Milestone:** 
**Generated:** 

### Obtain key

**Service:** 
**Status:** collected
**Destination:** dotenv

1. Go to the LLM provider's API dashboard
2. Create a new API key with appropriate quota
3. Copy the key value (starts with `sk-...`)
4. The execute unit will use `secure_env_collect` to inject the key into `.env`
