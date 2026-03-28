# Offline LLM And Analyst Playbooks

This layer sends only structured incident evidence to a local or secured remote LLM and returns analyst-only, approval-required playbooks.

## Implemented capabilities

- local LLM client for Ollama
- secure remote-node client with authenticated request headers and optional request signing
- strict structured evidence packaging
- analyst-only playbook generation with human approval required
- fallback playbook generation when the LLM is unavailable

## Main files

- [llm_service/client/ollama_client.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/llm_service/client/ollama_client.py)
- [llm_service/client/remote_secure_client.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/llm_service/client/remote_secure_client.py)
- [llm_service/secure_channel/request_signer.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/llm_service/secure_channel/request_signer.py)
- [playbook_generation/serializers/evidence_serializer.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/playbook_generation/serializers/evidence_serializer.py)
- [playbook_generation/recommendations/playbook_generator.py](C:/Users/sejal/OneDrive/Desktop/TrustSphere-SOC/playbook_generation/recommendations/playbook_generator.py)

## Security model

- only prioritized `llm_eligible` incidents are sent forward
- only structured evidence fields are packaged
- raw uncontrolled log blobs are not sent to the LLM
- remote mode supports authenticated headers and HMAC request signing
- playbooks are marked `analyst_only` and `approval_required`
