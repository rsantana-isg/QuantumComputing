#!/usr/bin/env python
# Author: corbett@caltech.edu

import numpy as np
import unittest
import re
import random
import exceptions
import itertools
from math import sqrt,pi,e,log
####
## Gates
####
class Gate(object):
	i_=np.complex(0,1)
	## One qubit gates
	# Hadamard gate
	H=1./sqrt(2)*np.matrix('1 1; 1 -1') 
	# Pauli gates
	X=np.matrix('0 1; 1 0')
	Y=np.matrix([[0, -i_],[i_, 0]])
	Z=np.matrix([[1,0],[0,-1]])

	# Defined as part of the Bell state experiment
	W=1/sqrt(2)*(X+Z)
	V=1/sqrt(2)*(-X+Z)
	
	# Other useful gates
	eye=np.eye(2,2)

	S=np.matrix([[1,0],[0,i_]])
	Sdagger=np.matrix([[1,0],[0,-i_]]) # convenience Sdagger = S.conjugate().transpose()

	T=np.matrix([[1,0],[0, e**(i_*pi/4.)]])
	Tdagger=np.matrix([[1,0],[0, e**(-i_*pi/4.)]]) # convenience Tdagger= T.conjugate().transpose()

	## Two qubit gates
	# CNOT Gate (control is qubit 0, target qubit 1), this is the default CNOT gate
	# TODO: can I break this down as a tensor product of 2x2 gates? 
	CNOT=np.matrix('1 0 0 0; 0 1 0 0; 0 0 0 1; 0 0 1 0')
	# Later may want to remove these, but currently codifying knowledge
	# control is qubit 1 target is qubit 0 
	CNOT10=np.kron(H,H)*CNOT*np.kron(H,H) #=np.matrix('1 0 0 0; 0 0 0 1; 0 0 1 0; 0 1 0 0') 
	# operates on 2/3 qubits, control is first subscript, target second
	CNOT3_01=np.kron(CNOT,eye)
	CNOT3_10=np.kron(CNOT10,eye)
	CNOT3_12=np.kron(eye,CNOT)
	CNOT3_21=np.kron(eye,CNOT10)
	# TODO: can I break this down as a tensor product?
	CNOT3_02=np.matrix('1 0 0 0 0 0 0 0; 0 1 0 0 0 0 0 0; 0 0 1 0 0 0 0 0; 0 0 0 1 0 0 0 0; 0 0 0 0 0 1 0 0; 0 0 0 0 1 0 0 0; 0 0 0 0 0 0 0 1; 0 0 0 0 0 0 1 0')
	CNOT3_20=np.matrix('1 0 0 0 0 0 0 0; 0 0 0 0 0 1 0 0; 0 0 1 0 0 0 0 0; 0 0 0 0 0 0 0 1; 0 0 0 0 1 0 0 0; 0 1 0 0 0 0 0 0; 0 0 0 0 0 0 1 0; 0 0 0 1 0 0 0 0')

####
## States
####
class State(object):
	i_=np.complex(0,1)
	## One qubit states (basis)
	# standard basis (z)
	zero_state=np.matrix('1; 0')
	one_state=np.matrix('0; 1')
	# diagonal basis (x)
	plus_state=1/sqrt(2)*np.matrix('1; 1')
	minus_state=1/sqrt(2)*np.matrix('1; -1')
	# circular basis (y)
	plusi_state=1/sqrt(2)*np.matrix([[1],[i_]])    # also known as clockwise arrow state
	minusi_state=1/sqrt(2)*np.matrix([[1],[-i_]])  # also known as counterclockwise arrow state

	# 2-qubit states
	bell_state=1/sqrt(2)*np.matrix('1; 0; 0; 1')
	@staticmethod
	def change_to_x_basis(state):
		return Gate.H*state

	@staticmethod
	def change_to_y_basis(state):
		return Gate.H*Gate.Sdagger*state

	@staticmethod
	def change_to_w_basis(state):
		# W=1/sqrt(2)*(X+Z)
		return Gate.H*Gate.T*Gate.H*Gate.S*state

	@staticmethod
	def change_to_v_basis(state):
		# V=1/sqrt(2)*(-X+Z)
		return Gate.H*Gate.Tdagger*Gate.H*Gate.S*state

	@staticmethod 
	def is_separable(qubit_state):
		try:
			State.separate_state(qubit_state)
			return True
		except StateNotSeparableException, e:
			return False

	@staticmethod
	def get_first_qubit(qubit_state):
		return State.separate_state(qubit_state)[0]

	@staticmethod
	def get_second_qubit(qubit_state):
		return State.separate_state(qubit_state)[1]

	@staticmethod
	def get_third_qubit(qubit_state):
		return State.separate_state(qubit_state)[2]

	@staticmethod
	def get_fourth_qubit(qubit_state):
		return State.separate_state(qubit_state)[3]

	@staticmethod
	def get_fifth_qubit(qubit_state):
		return State.separate_state(qubit_state)[4]

	@staticmethod 
	def all_state_strings(n_qubits):
		return [''.join(map(str,state_desc)) for state_desc in itertools.product([0, 1], repeat=n_qubits)]

	@staticmethod
	def state_from_string(qubit_state_string):
		if not all(x in '01' for x in qubit_state_string):
			raise Exception("Description must be a string in binary")
		state=None
		for qubit in qubit_state_string:
			if qubit=='0':
				new_contrib=State.zero_state
			elif qubit=='1':
				new_contrib=State.one_state
			if state==None:
				state=new_contrib
			else:
				state=np.kron(state,new_contrib)
		return state

	@staticmethod
	def string_from_state(qubit_state):
		separated=State.separate_state(qubit_state)
		desc=''
		for state in separated:
			if np.allclose(state,State.zero_state):
				desc+='0'
			elif np.allclose(state,State.one_state):
				desc+='1'
			else: 
				raise StateNotSeparableException("State is not separable")
		return desc

	@staticmethod
	def separate_state(qubit_state):
		"""This only works if the state is fully separable at present

		Throws exception if not a separable state"""
		n_entangled=Qubit.num_qubits(qubit_state)
		if list(qubit_state.flat).count(1)!=1:
			raise StateNotSeparableException("TODO: Entangled qubits not represented yet in quantum computer implementation. Can currently do manual calculations; see TestBellState for Examples")
		separated_state=[]
		idx_state=list(qubit_state.flat).index(1)
		add_factor=0
		size=qubit_state.shape[0]
		while(len(separated_state)<n_entangled):
			size=size/2
			if idx_state<(add_factor+size):
				separated_state+=[State.zero_state]
				add_factor+=0
			else:
				separated_state+=[State.one_state]
				add_factor+=size
		return separated_state

	@staticmethod
	def measure(state):
		"""finally some probabilities, whee. To properly use, set the qubit you measure to the result of this function
			to collapse it. state=measure(state). Currently supports only up to three entangled qubits """
		state_z=state
		n_qubits=Qubit.num_qubits(state)
		probs=Probability.get_probabilities(state_z)
		rand=random.random()
		for idx,state_desc in enumerate(State.all_state_strings(n_qubits)):
			if rand < sum(probs[0:(idx+1)]):
				return State.state_from_string(state_desc)

	@staticmethod
	def get_bloch(state):
		return np.array((Probability.expectation_x(state),Probability.expectation_y(state),Probability.expectation_z(state)))

class StateNotSeparableException(exceptions.Exception):
	def __init__(self,args=None):
		self.args=args

class Probability(object):
	@staticmethod
	def get_probability(coeff):
		return (coeff*coeff.conjugate()).real

	@staticmethod
	def get_probabilities(state):
		return [Probability.get_probability(x) for x in state.flat]

	@staticmethod
	def get_correlated_expectation(state):
		probs=Probability.get_probabilities(state)
		return probs[0]+probs[3]-probs[1]-probs[2]

	@staticmethod
	def pretty_print_probabilities(state):
		probs=Probability.get_probabilities(state)
		am_desc='|psi>='
		pr_desc=''
		for am,pr,state_desc in zip(state.flat,probs,State.all_state_strings(Qubit.num_qubits(state))):
			if am!=0:
				if am!=1:
					am_desc+='%r|%s>+'%(am,state_desc)
				else:
					am_desc+='|%s>+'%(am,state_desc)
			if pr!=0:
				pr_desc+='Pr(|%s>)|=%f; '%(state_desc,pr)
		print am_desc[0:-1]
		print pr_desc
		if state.shape==(4,1):
			print "<state>=%f" % probs[0]+probs[3]-probs[1]-probs[2]

	@staticmethod
	def expectation_x(state):
		state_x=State.change_to_x_basis(state)
		prob_zero_state=(state_x.item(0)*state_x.item(0).conjugate()).real
		prob_one_state=(state_x.item(1)*state_x.item(1).conjugate()).real
		return prob_zero_state-prob_one_state	

	@staticmethod
	def expectation_y(state):
		state_y=State.change_to_y_basis(state)
		prob_zero_state=(state_y.item(0)*state_y.item(0).conjugate()).real
		prob_one_state=(state_y.item(1)*state_y.item(1).conjugate()).real
		return prob_zero_state-prob_one_state

	@staticmethod
	def expectation_z(state):
		state_z=state
		prob_zero_state=(state_z.item(0)*state_z.item(0).conjugate()).real
		prob_one_state=(state_z.item(1)*state_z.item(1).conjugate()).real
		return prob_zero_state-prob_one_state

class Qubit(object):
	def __init__(self,name,state=State.zero_state,entangled=None):
		self.entangled=None
		self.state=state
		self.name = name
		self.noop = [] # after a measurement set this so that we can allow no further operations. Set to Bloch coords if bloch operation performed
	@staticmethod
	def num_qubits(state):	
		num_qubits=log(state.shape[0],2)
		if state.shape[1]!=1 or num_qubits not in [1,2,3,4,5]:
			raise Exception("unrecognized state shape")
		else:
			return int(num_qubits)
	def get_num_qubits(self):
		return Qubit.num_qubits(self.state)
	def __eq__(self,other):
		return self.name==other.name and np.allclose(self.noop,other.noop) and np.allclose(self.state,other.state) and (self.entangled==other.entangled==None or set(self.entangled)==set(other.entangled)) 

class QubitCollection(object):
	def __init__(self,qubits):
		self.qubits={}
		for q in qubits:
			self.qubits[q.name]=q
	def get_qubit_named(self,name):
		if self.qubits.has_key(name):
			return self.qubits[name]
		else:
			for nm,qubit in self.qubits.items():
				if qubit.entangled and nm in qubit.entangled:
					return qubit
		raise Exception("qubit %s not found" % name)
	def remove_qubit_named(self,name):
		del self.qubits[name]
	
	def add_qubit(self,qubit):
		self.qubits[qubit.name]=qubit


class QuantumComputer(object):
	"""This class is meant to simulate the 5-qubit IBM quantum computer, 
		and be able to interpret the auto generated programs on the site."""
	def __init__(self):
		self.qubits=QubitCollection([Qubit("q0"),Qubit("q1"),Qubit("q2"),Qubit("q3"),Qubit("q4")])
	def reset(self):
		self.qubits=QubitCollection([Qubit("q0"),Qubit("q1"),Qubit("q2"),Qubit("q3"),Qubit("q4")])

	def qubit_states_equal(self,name,state):
		return np.allclose(self.qubits.get_qubit_named(name).state,state)

	def bloch_coords_equal(self,name,coords):
		return np.allclose(self.qubits.get_qubit_named(name).noop,coords)

	def apply_gate(self,gate,on_qubit_name):
		on_qubit=self.qubits.get_qubit_named(on_qubit_name)
		if on_qubit.noop:
			raise Exception("This qubit has been measured previously, no more gates allowed")
		if not on_qubit.entangled:
			if on_qubit.get_num_qubits()!=1:
				raise Exception("This qubit is not marked as entangled but it has an entangled state")
			on_qubit.state=gate*on_qubit.state
		else:
			if not on_qubit.get_num_qubits()>1:
				raise Exception("This qubit is marked as entangled but it does not have an entangled state")
			n_entangled=len(on_qubit.entangled)
			apply_gate_to_qubit_idx=(on_qubit.entangled).index(on_qubit_name)
			if apply_gate_to_qubit_idx==0:
				entangled_gate=gate
			else:
				entangled_gate=Gate.eye
			for i in range(1,n_entangled):
				if apply_gate_to_qubit_idx==i:
					entangled_gate=np.kron(entangled_gate,gate)
				else:
					entangled_gate=np.kron(entangled_gate,Gate.eye)
			on_qubit.state=entangled_gate*on_qubit.state

	def apply_two_qubit_gate_CNOT(self,first_qubit_name,second_qubit_name):
		""" Currently this only supports the CNOT gate!"""
		first_qubit=self.qubits.get_qubit_named(first_qubit_name)
		second_qubit=self.qubits.get_qubit_named(second_qubit_name)
		if first_qubit.noop or second_qubit.noop:
			raise Exception("Control or target qubit has been measured previously, no more gates allowed")
		if not first_qubit.entangled and not second_qubit.entangled:
			if first_qubit.get_num_qubits()!=1 or second_qubit.get_num_qubits()!=1:
				raise Exception("Both qubits are marked as not entangled but one or the other has an entangled state")
			# currently only supported if we only have one target qubit (ourselves) and output is easily separated
			combined_state=np.kron(first_qubit.state,second_qubit.state)
			new_state=Gate.CNOT*combined_state
			if State.is_separable(new_state):
				second_qubit.state=State.get_second_qubit(new_state)
			else:
				first_qubit.entangled=[first_qubit_name,second_qubit_name]
				self.qubits.remove_qubit_named(second_qubit_name)
				first_qubit.state = new_state
		else:
			raise Exception("We don't support other modes of two qubit gates yet")
	def bloch(self,qubit_name):
		on_qubit=self.qubits.get_qubit_named(qubit_name)
		on_qubit.noop=State.get_bloch(on_qubit.state)
	def measure(self,qubit_name):
		on_qubit=self.qubits.get_qubit_named(qubit_name)
		if len(on_qubit.noop)==0:
			on_qubit.noop=on_qubit.state # state before measurement for testing
			on_qubit.state=State.measure(on_qubit.state)

	def execute(self,program):
		"""Time for some very lazy meta programming!
		"""
		# Transforming IBM's language to my variables
		lines=program.split(';')
		translation=[
			['q[0]','"q0"'],
			['q[1]','"q1"'],
			['q[2]','"q2"'],
			['q[3]','"q3"'],
			['q[4]','"q4"'],
			['bloch ',r'self.bloch('],
			['measure ',r'self.measure('],
			['id ','self.apply_gate(Gate.eye,'],
			['sdg ','self.apply_gate(Gate.Sdagger,'],
			['tdg ','self.apply_gate(Gate.Tdagger,'],
			['h ','self.apply_gate(Gate.H,'],
			['t ','self.apply_gate(Gate.T,'],
			['s ','self.apply_gate(Gate.S,'],
			['x ','self.apply_gate(Gate.X,'],
			['y ','self.apply_gate(Gate.Y,'],
			['z ','self.apply_gate(Gate.Z,'],
			]
		cnot_re=re.compile('^cx (q\[[0-4]\]), (q\[[0-4]\])$')
		for l in lines:
			l=l.strip()
			if not l: continue
			# CNOT operates on two qubits so gets special processing
			cnot=cnot_re.match(l)
			if cnot:
				control_qubit=cnot.group(1)
				target_qubit=cnot.group(2)
				l='self.apply_two_qubit_gate_CNOT(%s,%s'%(control_qubit,target_qubit)
			for k,v in translation:
				l=l.replace(k,v)
			l=l+')'
			# Now running the code
			exec l


class Program(object):
	def __init__(self,code,result_probability=[]):
		self.code=code

class Programs(object):
	"""Some useful programs collected in one place for running on the quantum computer class"""
	program_blue_state=Program("""h q[1];
			t q[1];
			h q[1];
			t q[1];
			h q[1];
			t q[1];
			s q[1];
			h q[1];
			t q[1];
			h q[1];
			t q[1];
			s q[1];
			h q[1];
			bloch q[1];""")
	program_test_XYZMeasureIdSdagTdag=Program("""sdg q[0];
			x q[1];
			x q[2];
			id q[3];
			z q[4];
			tdg q[0];
			y q[4];
			measure q[0];
			measure q[1];
			measure q[2];
			measure q[3];
			measure q[4];""")
	program_test_cnot=Program("""x q[1];
			cx q[1], q[2];""")
	program_test_many=Program("""sdg q[0];
			x q[1];
			x q[2];
			id q[3];
			z q[4];
			tdg q[0];
			cx q[1], q[2];
			y q[4];
			measure q[0];
			measure q[1];
			measure q[2];
			measure q[3];
			measure q[4];""")
	program_zz=Program("""h q[1];
		cx q[1], q[2];
		measure q[1];
		measure q[2];""") # "00",0.5; "11",0.5 # <zz> = 2

	program_zw=Program("""h q[1];
		cx q[1], q[2];
		s q[2];
		h q[2];
		t q[2];
		h q[2];
		measure q[1];
		measure q[2]""") # "00",0.426777; "01",0.073223; "10",0.073223; "11",0.426777 # <zw> = 1/sqrt(2)

	program_zv=Program("""h q[1];
		cx q[1], q[2];
		s q[2];
		h q[2];
		tdg q[2];
		h q[2];
		measure q[1];
		measure q[2];""") #"00",0.426777; "01",0.073223; "10",0.073223; "11",0.426777 # <zv> = 1/sqrt(2)

	program_xw=Program("""h q[1];
		cx q[1], q[2];
		h q[1];
		s q[2];
		h q[2];
		t q[2];
		h q[2];
		measure q[1];
		measure q[2];""") # "00",0.426777; "01",0.073223; "10",0.073223; "11",0.426777 # <xw> = 

	program_xv=Program("""h q[1];
		cx q[1], q[2];
		h q[1];
		s q[2];
		h q[2];
		tdg q[2];
		h q[2];
		measure q[1];
		measure q[2];""") #"00",0.073223; "01",0.426777; "10",0.426777; "11",0.073223; # <xv> =
	# Currently not used, but creats a superposition of 00 and 01
	program_00_01_super=Program("""sdg q[1];
		t q[1];
		t q[1];
		s q[1];
		h q[1];
		h q[0];
		h q[1];
		h q[0];
		h q[1];
		cx q[0], q[1];
		measure q[0];
		measure q[1];""")

	program_ghz=Program("""h q[0];
		h q[1];
		x q[2];
		cx q[1], q[2];
		cx q[0], q[2];
		h q[0];
		h q[1];
		h q[2];
		measure q[0];
		measure q[1];
		measure q[2];""")# "000":0.5; "111":0.5


	# now we measure it
	program_ghz_measure_yyx=Program("""h q[0];
		h q[1];
		x q[2];
		cx q[1], q[2];
		cx q[0], q[2];
		h q[0];
		h q[1];
		h q[2];
		sdg q[0];
		sdg q[1];
		h q[2];
		h q[0];
		h q[1];
		measure q[2];
		measure q[0];
		measure q[1];""") # "000":0.25; "011": 0.25; "101": 0.25; "110":0.25

	program_ghz_measure_yxy=Program("""h q[0];
		h q[1];
		x q[2];
		cx q[1], q[2];
		cx q[0], q[2];
		h q[0];
		h q[1];
		h q[2];
		sdg q[0];
		h q[1];
		sdg q[2];
		h q[0];
		measure q[1];
		h q[2];
		measure q[0];
		measure q[2];""") # "000":0.25; "011": 0.25; "101": 0.25; "110":0.25

	program_ghz_measure_xyy=Program("""h q[0];
		h q[1];
		x q[2];
		cx q[1], q[2];
		cx q[0], q[2];
		h q[0];
		h q[1];
		h q[2];
		h q[0];
		sdg q[1];
		sdg q[2];
		measure q[0];
		h q[1];
		h q[2];
		measure q[1];
		measure q[2];""") # "000":0.25; "011": 0.25; "101": 0.25; "110":0.25

	program_ghz_measure_xxx=Program("""h q[0];
		h q[1];
		x q[2];
		cx q[1], q[2];
		cx q[0], q[2];
		h q[0];
		h q[1];
		h q[2];
		h q[0];
		h q[1];
		h q[2];
		measure q[0];
		measure q[1];
		measure q[2];""") #"001":0.25; "010": 0.25; "100": 0.25; "111":0.25


#########################################################################################
# All test code below
#########################################################################################
class TestQubit(unittest.TestCase):
	def setUp(self):
		print "In method", self._testMethodName
	def setUp(self):
		self.q0 = Qubit("q0")
		self.q1 = Qubit("q1")
	def tearDown(self):
		self.q0=None
		self.q1=None
	def test_get_num_qubits(self):
		self.assertTrue(self.q0.get_num_qubits()==self.q0.get_num_qubits()==1)
	def test_equality(self):
		self.assertEqual(self.q0,self.q0)
		self.assertNotEqual(self.q0,self.q1)


class TestMeasure(unittest.TestCase):
	def setUp(self):
		print "In method", self._testMethodName
	def test_measure_probs_plus(self):
		measurements=[]
		for i in range(100000):
		 	measurements+=[State.measure(State.plus_state)]
		result=(1.*sum(measurements))/len(measurements)
		self.assertTrue(np.allclose(list(result.flat),np.array((0.5,0.5)),rtol=1e-2))
	def test_measure_probs_minus(self):
		measurements=[]
		for i in range(100000):
		 	measurements+=[State.measure(State.minus_state)]
		result=(1.*sum(measurements))/len(measurements)
		self.assertTrue(np.allclose(list(result.flat),np.array((0.5,0.5)),rtol=1e-2))
	def test_collapse(self):
		result=None
		for i in range(100):
			if result==None:
				result=State.measure(State.minus_state)
			else:
				new_measure=State.measure(result)
				self.assertTrue(np.allclose(result,new_measure))
				result=new_measure
	def test_measure_bell(self):
		""" Tests the measurement of a 2 qubit entangled system"""	
		measurements=[]
		for i in range(100000):
		 	measurements+=[State.measure(State.bell_state)]
		result=(1.*sum(measurements))/len(measurements)
		self.assertTrue(np.allclose(list(result.flat),np.array((0.5,0.0,0.0,0.5)),rtol=1e-2))

class TestGetBloch(unittest.TestCase):
	def setUp(self):
		print "In method", self._testMethodName
	def test_get_bloch(self):
		self.assertTrue(np.allclose(State.get_bloch(State.zero_state),np.array((0,0,1))))
		self.assertTrue(np.allclose(State.get_bloch(State.one_state),np.array((0,0,-1))))
		self.assertTrue(np.allclose(State.get_bloch(State.plusi_state),np.array((0,1,0))))
		self.assertTrue(np.allclose(State.get_bloch(State.minusi_state),np.array((0,-1,0))))
		self.assertTrue(np.allclose(State.get_bloch(Gate.Z*State.plus_state),np.array((-1,0,0))))
		self.assertTrue(np.allclose(State.get_bloch(Gate.Z*State.minus_state),np.array((1,0,0))))

		# assert the norms are 1 for cardinal points (obviously) but also for a few other points at higher T depth on the Bloch Sphere
		for state in [State.zero_state,State.one_state,State.plusi_state,State.minusi_state,Gate.Z*State.plus_state,Gate.H*Gate.T*Gate.Z*State.plus_state,Gate.H*Gate.T*Gate.H*Gate.T*Gate.H*Gate.T*Gate.Z*State.plus_state]:
			self.assertAlmostEqual(np.linalg.norm(state),1.0)

class TestGetBloch2(unittest.TestCase):
	def setUp(self):
		print "In method", self._testMethodName
	def get_bloch_2(self,state):
		""" equal to get_bloch just a different way of calculating things. Used for testing get_bloch. """
		return np.array((((state*state.conjugate().transpose()*Gate.X).trace()).item(0),((state*state.conjugate().transpose()*Gate.Y).trace()).item(0),((state*state.conjugate().transpose()*Gate.Z).trace()).item(0)))

	def test_get_bloch_2(self):
		self.assertTrue(np.allclose(self.get_bloch_2(State.zero_state),State.get_bloch(State.zero_state)))
		self.assertTrue(np.allclose(self.get_bloch_2(State.one_state),State.get_bloch(State.one_state)))
		self.assertTrue(np.allclose(self.get_bloch_2(State.plusi_state),State.get_bloch(State.plusi_state)))
		self.assertTrue(np.allclose(self.get_bloch_2(State.minusi_state),State.get_bloch(State.minusi_state)))
		self.assertTrue(np.allclose(self.get_bloch_2(Gate.Z*State.plus_state),State.get_bloch(Gate.Z*State.plus_state)))
		self.assertTrue(np.allclose(self.get_bloch_2(Gate.H*Gate.T*Gate.Z*State.plus_state),State.get_bloch(Gate.H*Gate.T*Gate.Z*State.plus_state))) # test for arbitrary gates


class TestCNOTGate(unittest.TestCase):	
	def setUp(self):
		print "In method", self._testMethodName
	def test_CNOT(self):
		self.assertTrue(np.allclose(Gate.CNOT*State.state_from_string('00'),State.state_from_string('00')))
		self.assertTrue(np.allclose(Gate.CNOT*State.state_from_string('01'),State.state_from_string('01')))
		self.assertTrue(np.allclose(Gate.CNOT*State.state_from_string('10'),State.state_from_string('11')))
		self.assertTrue(np.allclose(Gate.CNOT*State.state_from_string('11'),State.state_from_string('10')))

class TestTGate(unittest.TestCase):
	def setUp(self):
		print "In method", self._testMethodName
	def test_T(self):
		# This is useful to check some of the exercises on IBM's quantum experience. 
		# "Ground truth" answers from IBM's calculations which unfortunately are not reported to high precision.
		red_state=Gate.S*Gate.T*Gate.H*Gate.T*Gate.H*State.zero_state
		green_state=Gate.S*Gate.H*Gate.T*Gate.H*Gate.T*Gate.H*Gate.T*Gate.H*Gate.S*Gate.T*Gate.H*Gate.T*Gate.H*State.zero_state
		blue_state=Gate.H*Gate.S*Gate.T*Gate.H*Gate.T*Gate.H*Gate.S*Gate.T*Gate.H*Gate.T*Gate.H*Gate.T*Gate.H*State.zero_state
		self.assertTrue(np.allclose(State.get_bloch(red_state),np.array((0.5,0.5,0.707)),rtol=1e-3))
		self.assertTrue(np.allclose(State.get_bloch(green_state),np.array((0.427,0.457,0.780)),rtol=1e-3))
		self.assertTrue(np.allclose(State.get_bloch(blue_state),np.array((0.457,0.427,0.780)),rtol=1e-3))
		# Checking norms
		for state in [red_state,green_state,blue_state]:
			self.assertAlmostEqual(np.linalg.norm(state),1.0)

class TestMultiQubitStates(unittest.TestCase):
	def setUp(self):
		print "In method", self._testMethodName
		## Two qubit states (basis)
		# To derive the ordering you do ((+) is outer product):
		# Symbolically: |00> = |0> (+) |0>; gives 4x1 
		# In Python: np.kron(zero_state,zero_state)
		self.two_qubits_00=np.kron(State.zero_state,State.zero_state)
		self.two_qubits_01=np.kron(State.zero_state,State.one_state)
		self.two_qubits_10=np.kron(State.one_state,State.zero_state)
		self.two_qubits_11=np.kron(State.one_state,State.one_state)

		# # To operate a gate which operates on one qubit on elements of entangled 2-qubit state
		# # TODO: I think I should rather change the operator than the state, but this passes the test cases
		# qubits_00_state=two_qubits_00.reshape(2,2)
		# qubits_01_state=two_qubits_01.reshape(2,2)
		# qubits_10_state=two_qubits_10.reshape(2,2)
		# qubits_11_state=two_qubits_11.reshape(2,2)


		## Three qubit states (basis)
		self.three_qubits_000=np.kron(self.two_qubits_00,State.zero_state)
		self.three_qubits_001=np.kron(self.two_qubits_00,State.one_state)
		self.three_qubits_010=np.kron(self.two_qubits_01,State.zero_state)
		self.three_qubits_011=np.kron(self.two_qubits_01,State.one_state)
		self.three_qubits_100=np.kron(self.two_qubits_10,State.zero_state)
		self.three_qubits_101=np.kron(self.two_qubits_10,State.one_state)
		self.three_qubits_110=np.kron(self.two_qubits_11,State.zero_state)
		self.three_qubits_111=np.kron(self.two_qubits_11,State.one_state)

		# Four qubit states (basis)
		self.four_qubits_0000=np.kron(self.three_qubits_000,State.zero_state)
		self.four_qubits_0001=np.kron(self.three_qubits_000,State.one_state)
		self.four_qubits_0010=np.kron(self.three_qubits_001,State.zero_state)
		self.four_qubits_0011=np.kron(self.three_qubits_001,State.one_state)
		self.four_qubits_0100=np.kron(self.three_qubits_010,State.zero_state)
		self.four_qubits_0101=np.kron(self.three_qubits_010,State.one_state)
		self.four_qubits_0110=np.kron(self.three_qubits_011,State.zero_state)
		self.four_qubits_0111=np.kron(self.three_qubits_011,State.one_state)
		self.four_qubits_1000=np.kron(self.three_qubits_100,State.zero_state)
		self.four_qubits_1001=np.kron(self.three_qubits_100,State.one_state)
		self.four_qubits_1010=np.kron(self.three_qubits_101,State.zero_state)
		self.four_qubits_1011=np.kron(self.three_qubits_101,State.one_state)
		self.four_qubits_1100=np.kron(self.three_qubits_110,State.zero_state)
		self.four_qubits_1101=np.kron(self.three_qubits_110,State.one_state)
		self.four_qubits_1110=np.kron(self.three_qubits_111,State.zero_state)
		self.four_qubits_1111=np.kron(self.three_qubits_111,State.one_state)

		# Five qubit states (basis)
		self.five_qubits_00000=np.kron(self.four_qubits_0000,State.zero_state)
		self.five_qubits_00001=np.kron(self.four_qubits_0000,State.one_state)
		self.five_qubits_00010=np.kron(self.four_qubits_0001,State.zero_state)
		self.five_qubits_00011=np.kron(self.four_qubits_0001,State.one_state)
		self.five_qubits_00100=np.kron(self.four_qubits_0010,State.zero_state)
		self.five_qubits_00101=np.kron(self.four_qubits_0010,State.one_state)
		self.five_qubits_00110=np.kron(self.four_qubits_0011,State.zero_state)
		self.five_qubits_00111=np.kron(self.four_qubits_0011,State.one_state)
		self.five_qubits_01000=np.kron(self.four_qubits_0100,State.zero_state)
		self.five_qubits_01001=np.kron(self.four_qubits_0100,State.one_state)
		self.five_qubits_01010=np.kron(self.four_qubits_0101,State.zero_state)
		self.five_qubits_01011=np.kron(self.four_qubits_0101,State.one_state)
		self.five_qubits_01100=np.kron(self.four_qubits_0110,State.zero_state)
		self.five_qubits_01101=np.kron(self.four_qubits_0110,State.one_state)
		self.five_qubits_01110=np.kron(self.four_qubits_0111,State.zero_state)
		self.five_qubits_01111=np.kron(self.four_qubits_0111,State.one_state)
		self.five_qubits_10000=np.kron(self.four_qubits_1000,State.zero_state)
		self.five_qubits_10001=np.kron(self.four_qubits_1000,State.one_state)
		self.five_qubits_10010=np.kron(self.four_qubits_1001,State.zero_state)
		self.five_qubits_10011=np.kron(self.four_qubits_1001,State.one_state)
		self.five_qubits_10100=np.kron(self.four_qubits_1010,State.zero_state)
		self.five_qubits_10101=np.kron(self.four_qubits_1010,State.one_state)
		self.five_qubits_10110=np.kron(self.four_qubits_1011,State.zero_state)
		self.five_qubits_10111=np.kron(self.four_qubits_1011,State.one_state)
		self.five_qubits_11000=np.kron(self.four_qubits_1100,State.zero_state)
		self.five_qubits_11001=np.kron(self.four_qubits_1100,State.one_state)
		self.five_qubits_11010=np.kron(self.four_qubits_1101,State.zero_state)
		self.five_qubits_11011=np.kron(self.four_qubits_1101,State.one_state)
		self.five_qubits_11100=np.kron(self.four_qubits_1110,State.zero_state)
		self.five_qubits_11101=np.kron(self.four_qubits_1110,State.one_state)
		self.five_qubits_11110=np.kron(self.four_qubits_1111,State.zero_state)
		self.five_qubits_11111=np.kron(self.four_qubits_1111,State.one_state)

	def test_basis(self):
		# Sanity checks
		# 1-qubit
		self.assertTrue(np.allclose(State.zero_state+State.one_state,np.matrix('1; 1')))
		eye=np.eye(2,2)
		for row,state in enumerate([State.zero_state,State.one_state]):
			self.assertTrue(np.allclose(state.transpose(),eye[row]))
		# 2-qubit
		self.assertTrue(np.allclose(self.two_qubits_00+self.two_qubits_01+self.two_qubits_10+self.two_qubits_11,np.matrix('1; 1; 1; 1')))
		eye=np.eye(4,4)
		for row,state in enumerate([self.two_qubits_00,self.two_qubits_01,self.two_qubits_10,self.two_qubits_11]):
			self.assertTrue(np.allclose(state.transpose(),eye[row]))
		# 3-qubit
		self.assertTrue(np.allclose(self.three_qubits_000+self.three_qubits_001+self.three_qubits_010+self.three_qubits_011+self.three_qubits_100+self.three_qubits_101+self.three_qubits_110+self.three_qubits_111,np.matrix('1; 1; 1; 1; 1; 1; 1; 1')))
		eye=np.eye(8,8)
		for row,state in enumerate([self.three_qubits_000,self.three_qubits_001,self.three_qubits_010,self.three_qubits_011,self.three_qubits_100,self.three_qubits_101,self.three_qubits_110,self.three_qubits_111]):
			self.assertTrue(np.allclose(state.transpose(),eye[row]))
		# 4-qubit
		self.assertTrue(np.allclose(self.four_qubits_0000+self.four_qubits_0001+self.four_qubits_0010+self.four_qubits_0011+self.four_qubits_0100+self.four_qubits_0101+self.four_qubits_0110+self.four_qubits_0111+self.four_qubits_1000+self.four_qubits_1001+self.four_qubits_1010+self.four_qubits_1011+self.four_qubits_1100+self.four_qubits_1101+self.four_qubits_1110+self.four_qubits_1111,np.matrix('1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1')))
		eye=np.eye(16,16)
		for row,state in enumerate([self.four_qubits_0000,self.four_qubits_0001,self.four_qubits_0010,self.four_qubits_0011,self.four_qubits_0100,self.four_qubits_0101,self.four_qubits_0110,self.four_qubits_0111,self.four_qubits_1000,self.four_qubits_1001,self.four_qubits_1010,self.four_qubits_1011,self.four_qubits_1100,self.four_qubits_1101,self.four_qubits_1110,self.four_qubits_1111]):
			self.assertTrue(np.allclose(state.transpose(),eye[row]))
		# 5-qubit
		self.assertTrue(np.allclose(self.five_qubits_00000+self.five_qubits_00001+self.five_qubits_00010+self.five_qubits_00011+self.five_qubits_00100+self.five_qubits_00101+self.five_qubits_00110+self.five_qubits_00111+self.five_qubits_01000+self.five_qubits_01001+self.five_qubits_01010+self.five_qubits_01011+self.five_qubits_01100+self.five_qubits_01101+self.five_qubits_01110+self.five_qubits_01111+self.five_qubits_10000+self.five_qubits_10001+self.five_qubits_10010+self.five_qubits_10011+self.five_qubits_10100+self.five_qubits_10101+self.five_qubits_10110+self.five_qubits_10111+self.five_qubits_11000+self.five_qubits_11001+self.five_qubits_11010+self.five_qubits_11011+self.five_qubits_11100+self.five_qubits_11101+self.five_qubits_11110+self.five_qubits_11111,np.matrix('1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1; 1')))
		eye=np.eye(32,32)
		for row,state in enumerate([self.five_qubits_00000,self.five_qubits_00001,self.five_qubits_00010,self.five_qubits_00011,self.five_qubits_00100,self.five_qubits_00101,self.five_qubits_00110,self.five_qubits_00111,self.five_qubits_01000,self.five_qubits_01001,self.five_qubits_01010,self.five_qubits_01011,self.five_qubits_01100,self.five_qubits_01101,self.five_qubits_01110,self.five_qubits_01111,self.five_qubits_10000,self.five_qubits_10001,self.five_qubits_10010,self.five_qubits_10011,self.five_qubits_10100,self.five_qubits_10101,self.five_qubits_10110,self.five_qubits_10111,self.five_qubits_11000,self.five_qubits_11001,self.five_qubits_11010,self.five_qubits_11011,self.five_qubits_11100,self.five_qubits_11101,self.five_qubits_11110,self.five_qubits_11111]):
			self.assertTrue(np.allclose(state.transpose(),eye[row]))

	def test_separate_state(self):
		value_groups=[State.separate_state(self.five_qubits_11010),
			State.separate_state(self.four_qubits_0101),
			State.separate_state(self.three_qubits_000),
			State.separate_state(self.three_qubits_111),
			State.separate_state(self.three_qubits_101),
			State.separate_state(self.two_qubits_00),
			State.separate_state(self.two_qubits_01),
			State.separate_state(self.two_qubits_10),
			State.separate_state(self.two_qubits_11),
			State.separate_state(State.zero_state),
			State.separate_state(State.one_state)]

		target_groups=[(State.one_state,State.one_state,State.zero_state,State.one_state,State.zero_state),
			(State.zero_state,State.one_state,State.zero_state,State.one_state),
			(State.zero_state,State.zero_state,State.zero_state),
			(State.one_state,State.one_state,State.one_state),
			(State.one_state,State.zero_state,State.one_state),
			(State.zero_state,State.zero_state),
			(State.zero_state,State.one_state),
			(State.one_state,State.zero_state),
			(State.one_state,State.one_state),
			(State.zero_state),
			(State.one_state)]
		for vg,tg in zip(value_groups,target_groups):
			for value_state,target_state in zip(value_groups,target_groups):
				self.assertTrue(np.allclose(value_state,target_state)) 			

	def test_string_from_state(self):
		self.assertEqual(State.string_from_state(State.zero_state),'0')
		self.assertEqual(State.string_from_state(State.one_state),'1')
		self.assertEqual(State.string_from_state(self.two_qubits_00),'00')
		self.assertEqual(State.string_from_state(self.two_qubits_01),'01')
		self.assertEqual(State.string_from_state(self.two_qubits_10),'10')
		self.assertEqual(State.string_from_state(self.two_qubits_11),'11')
		self.assertEqual(State.string_from_state(self.three_qubits_110),'110')
		self.assertEqual(State.string_from_state(self.four_qubits_1101),'1101')
		self.assertEqual(State.string_from_state(self.five_qubits_11010),'11010')

	def test_state_from_string(self):
		for value_group,target_group in zip(['0','1','00','01','10','11','110','1101','11010'],
								[[State.zero_state],[State.one_state],[State.zero_state,State.zero_state],[State.zero_state,State.one_state],[State.one_state,State.zero_state],[State.one_state,State.one_state],[State.one_state,State.one_state,State.zero_state],[State.one_state,State.one_state,State.zero_state,State.one_state],[State.one_state,State.one_state,State.zero_state,State.one_state,State.zero_state]]):
			self.assertEqual(value_group,State.string_from_state(State.state_from_string(value_group)))
			value_group=State.separate_state(State.state_from_string(value_group))
			self.assertEqual(len(value_group),len(target_group)) 
			for value_state,target_state in zip(value_group,target_group):
				self.assertTrue(np.allclose(value_state,target_state)) 

class TestQuantumComputer(unittest.TestCase):
	def setUp(self):
		print "In method", self._testMethodName
		self.qc=QuantumComputer()
	def test_apply_gate(self):
		self.qc.apply_gate(Gate.H*Gate.T*Gate.Sdagger*Gate.Tdagger*Gate.X*Gate.Y,"q0")
		self.assertTrue(self.qc.qubit_states_equal("q0",Gate.H*Gate.T*Gate.Sdagger*Gate.Tdagger*Gate.X*Gate.Y*State.zero_state))
		# Some tests on entangled gates, breaking abstraction but will improve testing soon
		self.qc.reset()
		q0=self.qc.qubits.get_qubit_named("q0")
		q0.entangled=["q0","q1"]
		q0.state=np.kron(State.zero_state,State.zero_state)
		self.qc.qubits.remove_qubit_named("q1")

		# We will test applying the gate to qubits one and two
		self.qc.apply_gate(Gate.X,"q0")
		self.assertEqual(State.string_from_state(self.qc.qubits.get_qubit_named("q0").state),'10')
		self.qc.apply_gate(Gate.X,"q0")
		self.assertEqual(State.string_from_state(self.qc.qubits.get_qubit_named("q0").state),'00')

		self.assertEqual(self.qc.qubits.get_qubit_named("q1").name,"q0")
		self.qc.apply_gate(Gate.X,"q1")
		self.assertEqual(State.string_from_state(self.qc.qubits.get_qubit_named("q0").state),'01')
		self.qc.apply_gate(Gate.X,"q1")
		self.assertEqual(State.string_from_state(self.qc.qubits.get_qubit_named("q0").state),'00')
		self.qc.apply_gate(Gate.X,"q0")
		self.assertEqual(State.string_from_state(self.qc.qubits.get_qubit_named("q0").state),'10')
		self.qc.apply_gate(Gate.X,"q1")
		self.assertEqual(State.string_from_state(self.qc.qubits.get_qubit_named("q0").state),'11')

		# Now testing on 3 qubits
		q0.entangled=["q0","q1","q3"]
		q0.state=np.kron(np.kron(State.zero_state,State.zero_state),State.zero_state)
		self.qc.qubits.remove_qubit_named("q3")

		self.assertEqual(self.qc.qubits.get_qubit_named("q1").name,"q0")
		self.assertEqual(self.qc.qubits.get_qubit_named("q3").name,"q0")
		self.assertEqual(self.qc.qubits.get_qubit_named("q0").name,"q0")
		self.assertEqual(self.qc.qubits.get_qubit_named("q2").name,"q2")
		self.assertEqual(self.qc.qubits.get_qubit_named("q4").name,"q4")

		self.qc.apply_gate(Gate.X,"q0")
		self.assertEqual(State.string_from_state(self.qc.qubits.get_qubit_named("q0").state),'100')
		self.qc.apply_gate(Gate.X,"q0")
		self.assertEqual(State.string_from_state(self.qc.qubits.get_qubit_named("q0").state),'000')
		self.assertEqual(self.qc.qubits.get_qubit_named("q1").name,"q0")
		self.qc.apply_gate(Gate.X,"q1")
		self.assertEqual(State.string_from_state(self.qc.qubits.get_qubit_named("q0").state),'010')
		self.qc.apply_gate(Gate.X,"q1")
		self.assertEqual(State.string_from_state(self.qc.qubits.get_qubit_named("q0").state),'000')
		self.qc.apply_gate(Gate.X,"q0")
		self.assertEqual(State.string_from_state(self.qc.qubits.get_qubit_named("q0").state),'100')
		self.qc.apply_gate(Gate.X,"q1")
		self.assertEqual(State.string_from_state(self.qc.qubits.get_qubit_named("q0").state),'110')
		self.qc.apply_gate(Gate.X,"q3")
		self.assertEqual(State.string_from_state(self.qc.qubits.get_qubit_named("q0").state),'111')
		self.qc.apply_gate(Gate.X,"q1")
		self.assertEqual(State.string_from_state(self.qc.qubits.get_qubit_named("q0").state),'101')
		self.qc.apply_gate(Gate.X,"q4")
		self.assertEqual(State.string_from_state(self.qc.qubits.get_qubit_named("q4").state),'1')
		self.qc.apply_gate(Gate.X,"q4")
		self.assertEqual(State.string_from_state(self.qc.qubits.get_qubit_named("q4").state),'0')


	def test_apply_two_qubit_gate_CNOT_target(self):
		self.assertTrue(self.qc.qubit_states_equal("q0",State.zero_state))
		self.assertTrue(self.qc.qubit_states_equal("q1",State.zero_state))
		self.qc.apply_two_qubit_gate_CNOT("q0","q1")
		self.assertTrue(self.qc.qubit_states_equal("q0",State.zero_state))
		self.assertTrue(self.qc.qubit_states_equal("q1",State.zero_state))
		self.qc.apply_gate(Gate.X,"q0")
		self.qc.apply_two_qubit_gate_CNOT("q0","q1")
		self.assertTrue(self.qc.qubit_states_equal("q0",State.one_state))
		self.assertTrue(self.qc.qubit_states_equal("q1",State.one_state))
		self.qc.apply_two_qubit_gate_CNOT("q0","q1")
		self.assertTrue(self.qc.qubit_states_equal("q0",State.one_state))
		self.assertTrue(self.qc.qubit_states_equal("q1",State.zero_state))

	def test_execute_bluestate(self):
		"""Tests h,t,s,and bloch syntax on one qubit"""
		# This is a program to generate the 'blue state' in IBM's exercise
		self.qc.execute(Programs.program_blue_state.code)
		# check if we are in the blue state
		blue_state=Gate.H*Gate.S*Gate.T*Gate.H*Gate.T*Gate.H*Gate.S*Gate.T*Gate.H*Gate.T*Gate.H*Gate.T*Gate.H*State.zero_state
		self.assertTrue(self.qc.bloch_coords_equal("q1",State.get_bloch(blue_state)))
		# check to make sure we didn't change any other qubits in the QC

		for unchanged_state in ["q0","q2","q3","q4"]:
			self.assertTrue(self.qc.qubit_states_equal(unchanged_state,State.zero_state))
	def test_execute_X_Y_Z_Measure_Id_Sdag_Tdag(self):
		"""Tests z,y,measure,id,sdag,tdag syntax on all 5 qubits"""
		self.qc.execute(Programs.program_test_XYZMeasureIdSdagTdag.code)
		# result should be 01101
		self.assertTrue(self.qc.qubit_states_equal("q0",State.zero_state))
		self.assertTrue(self.qc.qubit_states_equal("q1",State.one_state))
		self.assertTrue(self.qc.qubit_states_equal("q2",State.one_state))
		self.assertTrue(self.qc.qubit_states_equal("q3",State.zero_state))
		self.assertTrue(self.qc.qubit_states_equal("q4",State.one_state))

	def test_execute_cnot(self):
		"""Tests cnot"""
		self.qc.execute(Programs.program_test_cnot.code)
		# result should be 01100
		self.assertTrue(self.qc.qubit_states_equal("q0",State.zero_state))
		self.assertTrue(self.qc.qubit_states_equal("q1",State.one_state))
		self.assertTrue(self.qc.qubit_states_equal("q2",State.one_state))
		self.assertTrue(self.qc.qubit_states_equal("q3",State.zero_state))
		self.assertTrue(self.qc.qubit_states_equal("q4",State.zero_state))


	def test_execute_many(self):
		"""Tests z,y,cnot,measure,id,sdag,tdag syntax on all 5 qubits"""
		self.qc.execute(Programs.program_test_many.code)
		# result should be 01001
		self.assertTrue(self.qc.qubit_states_equal("q0",State.zero_state))
		self.assertTrue(self.qc.qubit_states_equal("q1",State.one_state))
		self.assertTrue(self.qc.qubit_states_equal("q2",State.zero_state))
		self.assertTrue(self.qc.qubit_states_equal("q3",State.zero_state))
		self.assertTrue(self.qc.qubit_states_equal("q4",State.one_state))
	# These tests will be enabled after entanglement is supported properly
	# # Bell state experiments
	def test_bellstate_programs(self):
		# This tests two qubit entanglement.
		for program,result_probs,result_cor in zip([Programs.program_zz,Programs.program_zw,Programs.program_zv,Programs.program_xw,Programs.program_xv],
				[(0.5,0,0,0.5),(0.426777,0.073223,0.073223,0.426777),(0.426777,0.073223,0.073223,0.426777),(0.426777,0.073223,0.073223,0.426777),(0.073223,0.426777,0.426777,0.073223)],
				[1,1/sqrt(2),1/sqrt(2),1/sqrt(2),-1/sqrt(2)]):
			self.qc.reset()
			self.qc.execute(program.code)
			state_before_measure=self.qc.qubits.get_qubit_named("q1").noop
			probs=Probability.get_probabilities(state_before_measure)
			corex=Probability.get_correlated_expectation(state_before_measure)
			self.assertTrue(np.allclose(probs,result_probs))
			self.assertAlmostEqual(corex,result_cor)

	# def test_ghz_measurements(self):
		#This tests three qubit entaglement and measurement
		# self.qc.reset()
		# self.qc.execute(program_ghz)
		# ghz=self.qc.qubits.get_qubit_named("q1").noop
		# pr_ghz=Probability.get_probabilities(ghz)
		# self.assertTrue(np.allclose(pr_zz,(0.5,0,0,0,0,0,0,0.5)))
		# # 	# expectation of YYX should be n
		# # 	# expectation of YXY whould be n
		# # 	# expectation of XYY should be n
		# # 	# expectation of XXX should be -n
		# # 	# n ~ 3/4 TODO: calculate
		# # 	# M=expectation_yyx*expectation_yxy*expectation_xyy*expectation_xxx=~-0.2

	def tearDown(self):
		self.qc=None



if __name__ == '__main__':
 	unittest.main()
