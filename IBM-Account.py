from qiskit_ibm_runtime import QiskitRuntimeService
from dotenv import load_dotenv
import os


load_dotenv()
API_KEY = os.getenv("IBM_API_KEY")

QiskitRuntimeService.save_account(channel="ibm_quantum", token=API_KEY, overwrite=True, set_as_default=True)