
/**
 *  state_neuron.h
 *
 *  This file is part of NEST.
 *
 *  Copyright (C) 2004 The NEST Initiative
 *
 *  NEST is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  NEST is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with NEST.  If not, see <http://www.gnu.org/licenses/>.
 *
 *  Generated from NESTML 8.2.0 at time: 2025-11-13 19:20:20.490868
**/
#ifndef STATE_NEURON
#define STATE_NEURON

#ifndef HAVE_LIBLTDL
#error "NEST was compiled without support for dynamic loading. Please install libltdl and recompile NEST."
#endif

// C++ includes:
#include <cmath>

#include "config.h"

// Includes for random number generator
#include <random>

// Includes from nestkernel:
#include "archiving_node.h"
#include "connection.h"
#include "dict_util.h"
#include "event.h"
#include "nest_types.h"
#include "ring_buffer.h"
#include "universal_data_logger.h"

// Includes from sli:
#include "dictdatum.h"

// uncomment the next line to enable printing of detailed debug information
// #define DEBUG

namespace nest
{
namespace state_neuron_names
{
    const Name _in_rate( "in_rate" );
    const Name _out_rate( "out_rate" );
    const Name _spike_count_out( "spike_count_out" );
    const Name _current_fbk_input( "current_fbk_input" );
    const Name _current_pred_input( "current_pred_input" );
    const Name _fbk_buffer( "fbk_buffer" );
    const Name _pred_buffer( "pred_buffer" );
    const Name _fbk_counts( "fbk_counts" );
    const Name _pred_counts( "pred_counts" );
    const Name _tick( "tick" );
    const Name _position_count( "position_count" );
    const Name _mean_fbk( "mean_fbk" );
    const Name _mean_pred( "mean_pred" );
    const Name _var_fbk( "var_fbk" );
    const Name _var_pred( "var_pred" );
    const Name _CV_fbk( "CV_fbk" );
    const Name _CV_pred( "CV_pred" );
    const Name _total_CV( "total_CV" );
    const Name _lambda_poisson( "lambda_poisson" );
    const Name _kp( "kp" );
    const Name _pos( "pos" );
    const Name _base_rate( "base_rate" );
    const Name _buffer_size( "buffer_size" );
    const Name _simulation_steps( "simulation_steps" );
    const Name _N_fbk( "N_fbk" );
    const Name _N_pred( "N_pred" );
    const Name _fbk_bf_size( "fbk_bf_size" );
    const Name _pred_bf_size( "pred_bf_size" );
    const Name _time_wait( "time_wait" );
    const Name _time_trial( "time_trial" );

    const Name gsl_abs_error_tol("gsl_abs_error_tol");
    const Name gsl_rel_error_tol("gsl_rel_error_tol");
}
}




#include "nest_time.h"
  typedef size_t nest_port_t;
  typedef size_t nest_rport_t;

/* BeginDocumentation
  Name: state_neuron

  Description:

    

  Parameters:
  The following parameters can be set in the status dictionary.
kp [real]  Gain
pos [boolean]  Sign sensitivity of the neuron
base_rate [Hz]  Base firing rate
buffer_size [ms]  Size of the sliding window
simulation_steps [integer]  Number of simulation steps (simulation_time/resolution())
N_fbk [integer]  Population size for sensory feedback
N_pred [integer]  Population size for sensory prediction


  Dynamic state variables:
in_rate [Hz]  Input firing rate: to be computed from spikes
out_rate [Hz]  Output firing rate: defined accordingly to the input firing rate
spike_count_out [integer]  Outgoing spikes
fbk_buffer [real]  Buffer for sensory feedback spikes
pred_buffer [real]  Buffer for sensory prediction spikes
fbk_counts [real]  Counts of incoming feedback spikes
pred_counts [real]  Counts of incoming prediction spikes
tick [integer]  Tick 
mean_fbk [real]  Mean sensory feedback
mean_pred [real]  Mean sensory prediction
var_fbk [real]  Variance of sensory feedback
var_pred [real]  Variance of sensory prediction
CV_fbk [real]  Coefficient of variation of sensory feedback
CV_pred [real]  Coefficient of variation of sensory prediction
lambda_poisson [real]  Parameter of the Poisson distribution defining generator behavior


  Sends: nest::SpikeEvent

  Receives: Spike,  DataLoggingRequest
*/

// Register the neuron model
void register_state_neuron( const std::string& name );

class state_neuron : public nest::ArchivingNode
{
public:
  /**
   * The constructor is only used to create the model prototype in the model manager.
  **/
  state_neuron();

  /**
   * The copy constructor is used to create model copies and instances of the model.
   * @node The copy constructor needs to initialize the parameters and the state.
   *       Initialization of buffers and interal variables is deferred to
   *       @c init_buffers_() and @c pre_run_hook() (or calibrate() in NEST 3.3 and older).
  **/
  state_neuron(const state_neuron &);

  /**
   * Destructor.
  **/
  ~state_neuron() override;

  // -------------------------------------------------------------------------
  //   Import sets of overloaded virtual functions.
  //   See: Technical Issues / Virtual Functions: Overriding, Overloading,
  //        and Hiding
  // -------------------------------------------------------------------------

  using nest::Node::handles_test_event;
  using nest::Node::handle;

  /**
   * Used to validate that we can send nest::SpikeEvent to desired target:port.
  **/
  nest_port_t send_test_event(nest::Node& target, nest_rport_t receptor_type, nest::synindex, bool) override;


  // -------------------------------------------------------------------------
  //   Functions handling incoming events.
  //   We tell nest that we can handle incoming events of various types by
  //   defining handle() for the given event.
  // -------------------------------------------------------------------------


  void handle(nest::SpikeEvent &) override;        //! accept spikes

  void handle(nest::DataLoggingRequest &) override;//! allow recording with multimeter
  nest_port_t handles_test_event(nest::SpikeEvent&, nest_port_t) override;
  nest_port_t handles_test_event(nest::DataLoggingRequest&, nest_port_t) override;

  // -------------------------------------------------------------------------
  //   Functions for getting/setting parameters and state values.
  // -------------------------------------------------------------------------

  void get_status(DictionaryDatum &) const override;
  void set_status(const DictionaryDatum &) override;


  // -------------------------------------------------------------------------
  //   Getters/setters for state block
  // -------------------------------------------------------------------------

  inline double get_in_rate() const
  {
    return S_.in_rate;
  }

  inline void set_in_rate(const double __v)
  {
    S_.in_rate = __v;
  }

  inline double get_out_rate() const
  {
    return S_.out_rate;
  }

  inline void set_out_rate(const double __v)
  {
    S_.out_rate = __v;
  }

  inline long get_spike_count_out() const
  {
    return S_.spike_count_out;
  }

  inline void set_spike_count_out(const long __v)
  {
    S_.spike_count_out = __v;
  }

  inline std::vector< double >  get_current_fbk_input() const
  {
    return S_.current_fbk_input;
  }

  inline void set_current_fbk_input(const std::vector< double >  __v)
  {
    S_.current_fbk_input = __v;
  }

  inline std::vector< double >  get_current_pred_input() const
  {
    return S_.current_pred_input;
  }

  inline void set_current_pred_input(const std::vector< double >  __v)
  {
    S_.current_pred_input = __v;
  }

  inline std::vector< double >  get_fbk_buffer() const
  {
    return S_.fbk_buffer;
  }

  inline void set_fbk_buffer(const std::vector< double >  __v)
  {
    S_.fbk_buffer = __v;
  }

  inline std::vector< double >  get_pred_buffer() const
  {
    return S_.pred_buffer;
  }

  inline void set_pred_buffer(const std::vector< double >  __v)
  {
    S_.pred_buffer = __v;
  }

  inline std::vector< double >  get_fbk_counts() const
  {
    return S_.fbk_counts;
  }

  inline void set_fbk_counts(const std::vector< double >  __v)
  {
    S_.fbk_counts = __v;
  }

  inline std::vector< double >  get_pred_counts() const
  {
    return S_.pred_counts;
  }

  inline void set_pred_counts(const std::vector< double >  __v)
  {
    S_.pred_counts = __v;
  }

  inline long get_tick() const
  {
    return S_.tick;
  }

  inline void set_tick(const long __v)
  {
    S_.tick = __v;
  }

  inline long get_position_count() const
  {
    return S_.position_count;
  }

  inline void set_position_count(const long __v)
  {
    S_.position_count = __v;
  }

  inline double get_mean_fbk() const
  {
    return S_.mean_fbk;
  }

  inline void set_mean_fbk(const double __v)
  {
    S_.mean_fbk = __v;
  }

  inline double get_mean_pred() const
  {
    return S_.mean_pred;
  }

  inline void set_mean_pred(const double __v)
  {
    S_.mean_pred = __v;
  }

  inline double get_var_fbk() const
  {
    return S_.var_fbk;
  }

  inline void set_var_fbk(const double __v)
  {
    S_.var_fbk = __v;
  }

  inline double get_var_pred() const
  {
    return S_.var_pred;
  }

  inline void set_var_pred(const double __v)
  {
    S_.var_pred = __v;
  }

  inline double get_CV_fbk() const
  {
    return S_.CV_fbk;
  }

  inline void set_CV_fbk(const double __v)
  {
    S_.CV_fbk = __v;
  }

  inline double get_CV_pred() const
  {
    return S_.CV_pred;
  }

  inline void set_CV_pred(const double __v)
  {
    S_.CV_pred = __v;
  }

  inline double get_total_CV() const
  {
    return S_.total_CV;
  }

  inline void set_total_CV(const double __v)
  {
    S_.total_CV = __v;
  }

  inline double get_lambda_poisson() const
  {
    return S_.lambda_poisson;
  }

  inline void set_lambda_poisson(const double __v)
  {
    S_.lambda_poisson = __v;
  }


  // -------------------------------------------------------------------------
  //   Getters/setters for parameters
  // -------------------------------------------------------------------------

  inline double get_kp() const
  {
    return P_.kp;
  }

  inline void set_kp(const double __v)
  {
    P_.kp = __v;
  }

  inline bool get_pos() const
  {
    return P_.pos;
  }

  inline void set_pos(const bool __v)
  {
    P_.pos = __v;
  }

  inline double get_base_rate() const
  {
    return P_.base_rate;
  }

  inline void set_base_rate(const double __v)
  {
    P_.base_rate = __v;
  }

  inline double get_buffer_size() const
  {
    return P_.buffer_size;
  }

  inline void set_buffer_size(const double __v)
  {
    P_.buffer_size = __v;
  }

  inline long get_simulation_steps() const
  {
    return P_.simulation_steps;
  }

  inline void set_simulation_steps(const long __v)
  {
    P_.simulation_steps = __v;
  }

  inline long get_N_fbk() const
  {
    return P_.N_fbk;
  }

  inline void set_N_fbk(const long __v)
  {
    P_.N_fbk = __v;
  }

  inline long get_N_pred() const
  {
    return P_.N_pred;
  }

  inline void set_N_pred(const long __v)
  {
    P_.N_pred = __v;
  }

  inline long get_fbk_bf_size() const
  {
    return P_.fbk_bf_size;
  }

  inline void set_fbk_bf_size(const long __v)
  {
    P_.fbk_bf_size = __v;
  }

  inline long get_pred_bf_size() const
  {
    return P_.pred_bf_size;
  }

  inline void set_pred_bf_size(const long __v)
  {
    P_.pred_bf_size = __v;
  }

  inline double get_time_wait() const
  {
    return P_.time_wait;
  }

  inline void set_time_wait(const double __v)
  {
    P_.time_wait = __v;
  }

  inline double get_time_trial() const
  {
    return P_.time_trial;
  }

  inline void set_time_trial(const double __v)
  {
    P_.time_trial = __v;
  }


  // -------------------------------------------------------------------------
  //   Getters/setters for internals
  // -------------------------------------------------------------------------

  inline double get_res() const
  {
    return V_.res;
  }

  inline void set_res(const double __v)
  {
    V_.res = __v;
  }
  inline double get___h() const
  {
    return V_.__h;
  }

  inline void set___h(const double __v)
  {
    V_.__h = __v;
  }
  inline long get_buffer_steps() const
  {
    return V_.buffer_steps;
  }

  inline void set_buffer_steps(const long __v)
  {
    V_.buffer_steps = __v;
  }
  inline long get_trial_steps() const
  {
    return V_.trial_steps;
  }

  inline void set_trial_steps(const long __v)
  {
    V_.trial_steps = __v;
  }
  inline long get_wait_steps() const
  {
    return V_.wait_steps;
  }

  inline void set_wait_steps(const long __v)
  {
    V_.wait_steps = __v;
  }


  // -------------------------------------------------------------------------
  //   Methods corresponding to event handlers
  // -------------------------------------------------------------------------

  

  // -------------------------------------------------------------------------
  //   Initialization functions
  // -------------------------------------------------------------------------
  void calibrate_time( const nest::TimeConverter& tc ) override;

protected:

private:
  void recompute_internal_variables(bool exclude_timestep=false);

private:
/**
   * Synapse types to connect to
   * @note Excluded lower and upper bounds are defined as MIN_, MAX_.
   *       Excluding port 0 avoids accidental connections.
  **/
  static const nest_port_t MIN_SPIKE_RECEPTOR = 1;
  static const nest_port_t PORT_NOT_AVAILABLE = -1;

  enum SynapseTypes
  {
    FBK_SPIKES_0 = 1,
    FBK_SPIKES_1 = 2,
    FBK_SPIKES_2 = 3,
    FBK_SPIKES_3 = 4,
    FBK_SPIKES_4 = 5,
    FBK_SPIKES_5 = 6,
    FBK_SPIKES_6 = 7,
    FBK_SPIKES_7 = 8,
    FBK_SPIKES_8 = 9,
    FBK_SPIKES_9 = 10,
    FBK_SPIKES_10 = 11,
    FBK_SPIKES_11 = 12,
    FBK_SPIKES_12 = 13,
    FBK_SPIKES_13 = 14,
    FBK_SPIKES_14 = 15,
    FBK_SPIKES_15 = 16,
    FBK_SPIKES_16 = 17,
    FBK_SPIKES_17 = 18,
    FBK_SPIKES_18 = 19,
    FBK_SPIKES_19 = 20,
    FBK_SPIKES_20 = 21,
    FBK_SPIKES_21 = 22,
    FBK_SPIKES_22 = 23,
    FBK_SPIKES_23 = 24,
    FBK_SPIKES_24 = 25,
    FBK_SPIKES_25 = 26,
    FBK_SPIKES_26 = 27,
    FBK_SPIKES_27 = 28,
    FBK_SPIKES_28 = 29,
    FBK_SPIKES_29 = 30,
    FBK_SPIKES_30 = 31,
    FBK_SPIKES_31 = 32,
    FBK_SPIKES_32 = 33,
    FBK_SPIKES_33 = 34,
    FBK_SPIKES_34 = 35,
    FBK_SPIKES_35 = 36,
    FBK_SPIKES_36 = 37,
    FBK_SPIKES_37 = 38,
    FBK_SPIKES_38 = 39,
    FBK_SPIKES_39 = 40,
    FBK_SPIKES_40 = 41,
    FBK_SPIKES_41 = 42,
    FBK_SPIKES_42 = 43,
    FBK_SPIKES_43 = 44,
    FBK_SPIKES_44 = 45,
    FBK_SPIKES_45 = 46,
    FBK_SPIKES_46 = 47,
    FBK_SPIKES_47 = 48,
    FBK_SPIKES_48 = 49,
    FBK_SPIKES_49 = 50,
    FBK_SPIKES_50 = 51,
    FBK_SPIKES_51 = 52,
    FBK_SPIKES_52 = 53,
    FBK_SPIKES_53 = 54,
    FBK_SPIKES_54 = 55,
    FBK_SPIKES_55 = 56,
    FBK_SPIKES_56 = 57,
    FBK_SPIKES_57 = 58,
    FBK_SPIKES_58 = 59,
    FBK_SPIKES_59 = 60,
    FBK_SPIKES_60 = 61,
    FBK_SPIKES_61 = 62,
    FBK_SPIKES_62 = 63,
    FBK_SPIKES_63 = 64,
    FBK_SPIKES_64 = 65,
    FBK_SPIKES_65 = 66,
    FBK_SPIKES_66 = 67,
    FBK_SPIKES_67 = 68,
    FBK_SPIKES_68 = 69,
    FBK_SPIKES_69 = 70,
    FBK_SPIKES_70 = 71,
    FBK_SPIKES_71 = 72,
    FBK_SPIKES_72 = 73,
    FBK_SPIKES_73 = 74,
    FBK_SPIKES_74 = 75,
    FBK_SPIKES_75 = 76,
    FBK_SPIKES_76 = 77,
    FBK_SPIKES_77 = 78,
    FBK_SPIKES_78 = 79,
    FBK_SPIKES_79 = 80,
    FBK_SPIKES_80 = 81,
    FBK_SPIKES_81 = 82,
    FBK_SPIKES_82 = 83,
    FBK_SPIKES_83 = 84,
    FBK_SPIKES_84 = 85,
    FBK_SPIKES_85 = 86,
    FBK_SPIKES_86 = 87,
    FBK_SPIKES_87 = 88,
    FBK_SPIKES_88 = 89,
    FBK_SPIKES_89 = 90,
    FBK_SPIKES_90 = 91,
    FBK_SPIKES_91 = 92,
    FBK_SPIKES_92 = 93,
    FBK_SPIKES_93 = 94,
    FBK_SPIKES_94 = 95,
    FBK_SPIKES_95 = 96,
    FBK_SPIKES_96 = 97,
    FBK_SPIKES_97 = 98,
    FBK_SPIKES_98 = 99,
    FBK_SPIKES_99 = 100,
    FBK_SPIKES_100 = 101,
    FBK_SPIKES_101 = 102,
    FBK_SPIKES_102 = 103,
    FBK_SPIKES_103 = 104,
    FBK_SPIKES_104 = 105,
    FBK_SPIKES_105 = 106,
    FBK_SPIKES_106 = 107,
    FBK_SPIKES_107 = 108,
    FBK_SPIKES_108 = 109,
    FBK_SPIKES_109 = 110,
    FBK_SPIKES_110 = 111,
    FBK_SPIKES_111 = 112,
    FBK_SPIKES_112 = 113,
    FBK_SPIKES_113 = 114,
    FBK_SPIKES_114 = 115,
    FBK_SPIKES_115 = 116,
    FBK_SPIKES_116 = 117,
    FBK_SPIKES_117 = 118,
    FBK_SPIKES_118 = 119,
    FBK_SPIKES_119 = 120,
    FBK_SPIKES_120 = 121,
    FBK_SPIKES_121 = 122,
    FBK_SPIKES_122 = 123,
    FBK_SPIKES_123 = 124,
    FBK_SPIKES_124 = 125,
    FBK_SPIKES_125 = 126,
    FBK_SPIKES_126 = 127,
    FBK_SPIKES_127 = 128,
    FBK_SPIKES_128 = 129,
    FBK_SPIKES_129 = 130,
    FBK_SPIKES_130 = 131,
    FBK_SPIKES_131 = 132,
    FBK_SPIKES_132 = 133,
    FBK_SPIKES_133 = 134,
    FBK_SPIKES_134 = 135,
    FBK_SPIKES_135 = 136,
    FBK_SPIKES_136 = 137,
    FBK_SPIKES_137 = 138,
    FBK_SPIKES_138 = 139,
    FBK_SPIKES_139 = 140,
    FBK_SPIKES_140 = 141,
    FBK_SPIKES_141 = 142,
    FBK_SPIKES_142 = 143,
    FBK_SPIKES_143 = 144,
    FBK_SPIKES_144 = 145,
    FBK_SPIKES_145 = 146,
    FBK_SPIKES_146 = 147,
    FBK_SPIKES_147 = 148,
    FBK_SPIKES_148 = 149,
    FBK_SPIKES_149 = 150,
    FBK_SPIKES_150 = 151,
    FBK_SPIKES_151 = 152,
    FBK_SPIKES_152 = 153,
    FBK_SPIKES_153 = 154,
    FBK_SPIKES_154 = 155,
    FBK_SPIKES_155 = 156,
    FBK_SPIKES_156 = 157,
    FBK_SPIKES_157 = 158,
    FBK_SPIKES_158 = 159,
    FBK_SPIKES_159 = 160,
    FBK_SPIKES_160 = 161,
    FBK_SPIKES_161 = 162,
    FBK_SPIKES_162 = 163,
    FBK_SPIKES_163 = 164,
    FBK_SPIKES_164 = 165,
    FBK_SPIKES_165 = 166,
    FBK_SPIKES_166 = 167,
    FBK_SPIKES_167 = 168,
    FBK_SPIKES_168 = 169,
    FBK_SPIKES_169 = 170,
    FBK_SPIKES_170 = 171,
    FBK_SPIKES_171 = 172,
    FBK_SPIKES_172 = 173,
    FBK_SPIKES_173 = 174,
    FBK_SPIKES_174 = 175,
    FBK_SPIKES_175 = 176,
    FBK_SPIKES_176 = 177,
    FBK_SPIKES_177 = 178,
    FBK_SPIKES_178 = 179,
    FBK_SPIKES_179 = 180,
    FBK_SPIKES_180 = 181,
    FBK_SPIKES_181 = 182,
    FBK_SPIKES_182 = 183,
    FBK_SPIKES_183 = 184,
    FBK_SPIKES_184 = 185,
    FBK_SPIKES_185 = 186,
    FBK_SPIKES_186 = 187,
    FBK_SPIKES_187 = 188,
    FBK_SPIKES_188 = 189,
    FBK_SPIKES_189 = 190,
    FBK_SPIKES_190 = 191,
    FBK_SPIKES_191 = 192,
    FBK_SPIKES_192 = 193,
    FBK_SPIKES_193 = 194,
    FBK_SPIKES_194 = 195,
    FBK_SPIKES_195 = 196,
    FBK_SPIKES_196 = 197,
    FBK_SPIKES_197 = 198,
    FBK_SPIKES_198 = 199,
    FBK_SPIKES_199 = 200,
    FBK_SPIKES_200 = 201,
    FBK_SPIKES_201 = 202,
    FBK_SPIKES_202 = 203,
    FBK_SPIKES_203 = 204,
    FBK_SPIKES_204 = 205,
    FBK_SPIKES_205 = 206,
    FBK_SPIKES_206 = 207,
    FBK_SPIKES_207 = 208,
    FBK_SPIKES_208 = 209,
    FBK_SPIKES_209 = 210,
    FBK_SPIKES_210 = 211,
    FBK_SPIKES_211 = 212,
    FBK_SPIKES_212 = 213,
    FBK_SPIKES_213 = 214,
    FBK_SPIKES_214 = 215,
    FBK_SPIKES_215 = 216,
    FBK_SPIKES_216 = 217,
    FBK_SPIKES_217 = 218,
    FBK_SPIKES_218 = 219,
    FBK_SPIKES_219 = 220,
    FBK_SPIKES_220 = 221,
    FBK_SPIKES_221 = 222,
    FBK_SPIKES_222 = 223,
    FBK_SPIKES_223 = 224,
    FBK_SPIKES_224 = 225,
    FBK_SPIKES_225 = 226,
    FBK_SPIKES_226 = 227,
    FBK_SPIKES_227 = 228,
    FBK_SPIKES_228 = 229,
    FBK_SPIKES_229 = 230,
    FBK_SPIKES_230 = 231,
    FBK_SPIKES_231 = 232,
    FBK_SPIKES_232 = 233,
    FBK_SPIKES_233 = 234,
    FBK_SPIKES_234 = 235,
    FBK_SPIKES_235 = 236,
    FBK_SPIKES_236 = 237,
    FBK_SPIKES_237 = 238,
    FBK_SPIKES_238 = 239,
    FBK_SPIKES_239 = 240,
    FBK_SPIKES_240 = 241,
    FBK_SPIKES_241 = 242,
    FBK_SPIKES_242 = 243,
    FBK_SPIKES_243 = 244,
    FBK_SPIKES_244 = 245,
    FBK_SPIKES_245 = 246,
    FBK_SPIKES_246 = 247,
    FBK_SPIKES_247 = 248,
    FBK_SPIKES_248 = 249,
    FBK_SPIKES_249 = 250,
    FBK_SPIKES_250 = 251,
    FBK_SPIKES_251 = 252,
    FBK_SPIKES_252 = 253,
    FBK_SPIKES_253 = 254,
    FBK_SPIKES_254 = 255,
    FBK_SPIKES_255 = 256,
    FBK_SPIKES_256 = 257,
    FBK_SPIKES_257 = 258,
    FBK_SPIKES_258 = 259,
    FBK_SPIKES_259 = 260,
    FBK_SPIKES_260 = 261,
    FBK_SPIKES_261 = 262,
    FBK_SPIKES_262 = 263,
    FBK_SPIKES_263 = 264,
    FBK_SPIKES_264 = 265,
    FBK_SPIKES_265 = 266,
    FBK_SPIKES_266 = 267,
    FBK_SPIKES_267 = 268,
    FBK_SPIKES_268 = 269,
    FBK_SPIKES_269 = 270,
    FBK_SPIKES_270 = 271,
    FBK_SPIKES_271 = 272,
    FBK_SPIKES_272 = 273,
    FBK_SPIKES_273 = 274,
    FBK_SPIKES_274 = 275,
    FBK_SPIKES_275 = 276,
    FBK_SPIKES_276 = 277,
    FBK_SPIKES_277 = 278,
    FBK_SPIKES_278 = 279,
    FBK_SPIKES_279 = 280,
    FBK_SPIKES_280 = 281,
    FBK_SPIKES_281 = 282,
    FBK_SPIKES_282 = 283,
    FBK_SPIKES_283 = 284,
    FBK_SPIKES_284 = 285,
    FBK_SPIKES_285 = 286,
    FBK_SPIKES_286 = 287,
    FBK_SPIKES_287 = 288,
    FBK_SPIKES_288 = 289,
    FBK_SPIKES_289 = 290,
    FBK_SPIKES_290 = 291,
    FBK_SPIKES_291 = 292,
    FBK_SPIKES_292 = 293,
    FBK_SPIKES_293 = 294,
    FBK_SPIKES_294 = 295,
    FBK_SPIKES_295 = 296,
    FBK_SPIKES_296 = 297,
    FBK_SPIKES_297 = 298,
    FBK_SPIKES_298 = 299,
    FBK_SPIKES_299 = 300,
    FBK_SPIKES_300 = 301,
    FBK_SPIKES_301 = 302,
    FBK_SPIKES_302 = 303,
    FBK_SPIKES_303 = 304,
    FBK_SPIKES_304 = 305,
    FBK_SPIKES_305 = 306,
    FBK_SPIKES_306 = 307,
    FBK_SPIKES_307 = 308,
    FBK_SPIKES_308 = 309,
    FBK_SPIKES_309 = 310,
    FBK_SPIKES_310 = 311,
    FBK_SPIKES_311 = 312,
    FBK_SPIKES_312 = 313,
    FBK_SPIKES_313 = 314,
    FBK_SPIKES_314 = 315,
    FBK_SPIKES_315 = 316,
    FBK_SPIKES_316 = 317,
    FBK_SPIKES_317 = 318,
    FBK_SPIKES_318 = 319,
    FBK_SPIKES_319 = 320,
    FBK_SPIKES_320 = 321,
    FBK_SPIKES_321 = 322,
    FBK_SPIKES_322 = 323,
    FBK_SPIKES_323 = 324,
    FBK_SPIKES_324 = 325,
    FBK_SPIKES_325 = 326,
    FBK_SPIKES_326 = 327,
    FBK_SPIKES_327 = 328,
    FBK_SPIKES_328 = 329,
    FBK_SPIKES_329 = 330,
    FBK_SPIKES_330 = 331,
    FBK_SPIKES_331 = 332,
    FBK_SPIKES_332 = 333,
    FBK_SPIKES_333 = 334,
    FBK_SPIKES_334 = 335,
    FBK_SPIKES_335 = 336,
    FBK_SPIKES_336 = 337,
    FBK_SPIKES_337 = 338,
    FBK_SPIKES_338 = 339,
    FBK_SPIKES_339 = 340,
    FBK_SPIKES_340 = 341,
    FBK_SPIKES_341 = 342,
    FBK_SPIKES_342 = 343,
    FBK_SPIKES_343 = 344,
    FBK_SPIKES_344 = 345,
    FBK_SPIKES_345 = 346,
    FBK_SPIKES_346 = 347,
    FBK_SPIKES_347 = 348,
    FBK_SPIKES_348 = 349,
    FBK_SPIKES_349 = 350,
    FBK_SPIKES_350 = 351,
    FBK_SPIKES_351 = 352,
    FBK_SPIKES_352 = 353,
    FBK_SPIKES_353 = 354,
    FBK_SPIKES_354 = 355,
    FBK_SPIKES_355 = 356,
    FBK_SPIKES_356 = 357,
    FBK_SPIKES_357 = 358,
    FBK_SPIKES_358 = 359,
    FBK_SPIKES_359 = 360,
    FBK_SPIKES_360 = 361,
    FBK_SPIKES_361 = 362,
    FBK_SPIKES_362 = 363,
    FBK_SPIKES_363 = 364,
    FBK_SPIKES_364 = 365,
    FBK_SPIKES_365 = 366,
    FBK_SPIKES_366 = 367,
    FBK_SPIKES_367 = 368,
    FBK_SPIKES_368 = 369,
    FBK_SPIKES_369 = 370,
    FBK_SPIKES_370 = 371,
    FBK_SPIKES_371 = 372,
    FBK_SPIKES_372 = 373,
    FBK_SPIKES_373 = 374,
    FBK_SPIKES_374 = 375,
    FBK_SPIKES_375 = 376,
    FBK_SPIKES_376 = 377,
    FBK_SPIKES_377 = 378,
    FBK_SPIKES_378 = 379,
    FBK_SPIKES_379 = 380,
    FBK_SPIKES_380 = 381,
    FBK_SPIKES_381 = 382,
    FBK_SPIKES_382 = 383,
    FBK_SPIKES_383 = 384,
    FBK_SPIKES_384 = 385,
    FBK_SPIKES_385 = 386,
    FBK_SPIKES_386 = 387,
    FBK_SPIKES_387 = 388,
    FBK_SPIKES_388 = 389,
    FBK_SPIKES_389 = 390,
    FBK_SPIKES_390 = 391,
    FBK_SPIKES_391 = 392,
    FBK_SPIKES_392 = 393,
    FBK_SPIKES_393 = 394,
    FBK_SPIKES_394 = 395,
    FBK_SPIKES_395 = 396,
    FBK_SPIKES_396 = 397,
    FBK_SPIKES_397 = 398,
    FBK_SPIKES_398 = 399,
    FBK_SPIKES_399 = 400,
    PRED_SPIKES_0 = 401,
    PRED_SPIKES_1 = 402,
    PRED_SPIKES_2 = 403,
    PRED_SPIKES_3 = 404,
    PRED_SPIKES_4 = 405,
    PRED_SPIKES_5 = 406,
    PRED_SPIKES_6 = 407,
    PRED_SPIKES_7 = 408,
    PRED_SPIKES_8 = 409,
    PRED_SPIKES_9 = 410,
    PRED_SPIKES_10 = 411,
    PRED_SPIKES_11 = 412,
    PRED_SPIKES_12 = 413,
    PRED_SPIKES_13 = 414,
    PRED_SPIKES_14 = 415,
    PRED_SPIKES_15 = 416,
    PRED_SPIKES_16 = 417,
    PRED_SPIKES_17 = 418,
    PRED_SPIKES_18 = 419,
    PRED_SPIKES_19 = 420,
    PRED_SPIKES_20 = 421,
    PRED_SPIKES_21 = 422,
    PRED_SPIKES_22 = 423,
    PRED_SPIKES_23 = 424,
    PRED_SPIKES_24 = 425,
    PRED_SPIKES_25 = 426,
    PRED_SPIKES_26 = 427,
    PRED_SPIKES_27 = 428,
    PRED_SPIKES_28 = 429,
    PRED_SPIKES_29 = 430,
    PRED_SPIKES_30 = 431,
    PRED_SPIKES_31 = 432,
    PRED_SPIKES_32 = 433,
    PRED_SPIKES_33 = 434,
    PRED_SPIKES_34 = 435,
    PRED_SPIKES_35 = 436,
    PRED_SPIKES_36 = 437,
    PRED_SPIKES_37 = 438,
    PRED_SPIKES_38 = 439,
    PRED_SPIKES_39 = 440,
    PRED_SPIKES_40 = 441,
    PRED_SPIKES_41 = 442,
    PRED_SPIKES_42 = 443,
    PRED_SPIKES_43 = 444,
    PRED_SPIKES_44 = 445,
    PRED_SPIKES_45 = 446,
    PRED_SPIKES_46 = 447,
    PRED_SPIKES_47 = 448,
    PRED_SPIKES_48 = 449,
    PRED_SPIKES_49 = 450,
    PRED_SPIKES_50 = 451,
    PRED_SPIKES_51 = 452,
    PRED_SPIKES_52 = 453,
    PRED_SPIKES_53 = 454,
    PRED_SPIKES_54 = 455,
    PRED_SPIKES_55 = 456,
    PRED_SPIKES_56 = 457,
    PRED_SPIKES_57 = 458,
    PRED_SPIKES_58 = 459,
    PRED_SPIKES_59 = 460,
    PRED_SPIKES_60 = 461,
    PRED_SPIKES_61 = 462,
    PRED_SPIKES_62 = 463,
    PRED_SPIKES_63 = 464,
    PRED_SPIKES_64 = 465,
    PRED_SPIKES_65 = 466,
    PRED_SPIKES_66 = 467,
    PRED_SPIKES_67 = 468,
    PRED_SPIKES_68 = 469,
    PRED_SPIKES_69 = 470,
    PRED_SPIKES_70 = 471,
    PRED_SPIKES_71 = 472,
    PRED_SPIKES_72 = 473,
    PRED_SPIKES_73 = 474,
    PRED_SPIKES_74 = 475,
    PRED_SPIKES_75 = 476,
    PRED_SPIKES_76 = 477,
    PRED_SPIKES_77 = 478,
    PRED_SPIKES_78 = 479,
    PRED_SPIKES_79 = 480,
    PRED_SPIKES_80 = 481,
    PRED_SPIKES_81 = 482,
    PRED_SPIKES_82 = 483,
    PRED_SPIKES_83 = 484,
    PRED_SPIKES_84 = 485,
    PRED_SPIKES_85 = 486,
    PRED_SPIKES_86 = 487,
    PRED_SPIKES_87 = 488,
    PRED_SPIKES_88 = 489,
    PRED_SPIKES_89 = 490,
    PRED_SPIKES_90 = 491,
    PRED_SPIKES_91 = 492,
    PRED_SPIKES_92 = 493,
    PRED_SPIKES_93 = 494,
    PRED_SPIKES_94 = 495,
    PRED_SPIKES_95 = 496,
    PRED_SPIKES_96 = 497,
    PRED_SPIKES_97 = 498,
    PRED_SPIKES_98 = 499,
    PRED_SPIKES_99 = 500,
    PRED_SPIKES_100 = 501,
    PRED_SPIKES_101 = 502,
    PRED_SPIKES_102 = 503,
    PRED_SPIKES_103 = 504,
    PRED_SPIKES_104 = 505,
    PRED_SPIKES_105 = 506,
    PRED_SPIKES_106 = 507,
    PRED_SPIKES_107 = 508,
    PRED_SPIKES_108 = 509,
    PRED_SPIKES_109 = 510,
    PRED_SPIKES_110 = 511,
    PRED_SPIKES_111 = 512,
    PRED_SPIKES_112 = 513,
    PRED_SPIKES_113 = 514,
    PRED_SPIKES_114 = 515,
    PRED_SPIKES_115 = 516,
    PRED_SPIKES_116 = 517,
    PRED_SPIKES_117 = 518,
    PRED_SPIKES_118 = 519,
    PRED_SPIKES_119 = 520,
    PRED_SPIKES_120 = 521,
    PRED_SPIKES_121 = 522,
    PRED_SPIKES_122 = 523,
    PRED_SPIKES_123 = 524,
    PRED_SPIKES_124 = 525,
    PRED_SPIKES_125 = 526,
    PRED_SPIKES_126 = 527,
    PRED_SPIKES_127 = 528,
    PRED_SPIKES_128 = 529,
    PRED_SPIKES_129 = 530,
    PRED_SPIKES_130 = 531,
    PRED_SPIKES_131 = 532,
    PRED_SPIKES_132 = 533,
    PRED_SPIKES_133 = 534,
    PRED_SPIKES_134 = 535,
    PRED_SPIKES_135 = 536,
    PRED_SPIKES_136 = 537,
    PRED_SPIKES_137 = 538,
    PRED_SPIKES_138 = 539,
    PRED_SPIKES_139 = 540,
    PRED_SPIKES_140 = 541,
    PRED_SPIKES_141 = 542,
    PRED_SPIKES_142 = 543,
    PRED_SPIKES_143 = 544,
    PRED_SPIKES_144 = 545,
    PRED_SPIKES_145 = 546,
    PRED_SPIKES_146 = 547,
    PRED_SPIKES_147 = 548,
    PRED_SPIKES_148 = 549,
    PRED_SPIKES_149 = 550,
    PRED_SPIKES_150 = 551,
    PRED_SPIKES_151 = 552,
    PRED_SPIKES_152 = 553,
    PRED_SPIKES_153 = 554,
    PRED_SPIKES_154 = 555,
    PRED_SPIKES_155 = 556,
    PRED_SPIKES_156 = 557,
    PRED_SPIKES_157 = 558,
    PRED_SPIKES_158 = 559,
    PRED_SPIKES_159 = 560,
    PRED_SPIKES_160 = 561,
    PRED_SPIKES_161 = 562,
    PRED_SPIKES_162 = 563,
    PRED_SPIKES_163 = 564,
    PRED_SPIKES_164 = 565,
    PRED_SPIKES_165 = 566,
    PRED_SPIKES_166 = 567,
    PRED_SPIKES_167 = 568,
    PRED_SPIKES_168 = 569,
    PRED_SPIKES_169 = 570,
    PRED_SPIKES_170 = 571,
    PRED_SPIKES_171 = 572,
    PRED_SPIKES_172 = 573,
    PRED_SPIKES_173 = 574,
    PRED_SPIKES_174 = 575,
    PRED_SPIKES_175 = 576,
    PRED_SPIKES_176 = 577,
    PRED_SPIKES_177 = 578,
    PRED_SPIKES_178 = 579,
    PRED_SPIKES_179 = 580,
    PRED_SPIKES_180 = 581,
    PRED_SPIKES_181 = 582,
    PRED_SPIKES_182 = 583,
    PRED_SPIKES_183 = 584,
    PRED_SPIKES_184 = 585,
    PRED_SPIKES_185 = 586,
    PRED_SPIKES_186 = 587,
    PRED_SPIKES_187 = 588,
    PRED_SPIKES_188 = 589,
    PRED_SPIKES_189 = 590,
    PRED_SPIKES_190 = 591,
    PRED_SPIKES_191 = 592,
    PRED_SPIKES_192 = 593,
    PRED_SPIKES_193 = 594,
    PRED_SPIKES_194 = 595,
    PRED_SPIKES_195 = 596,
    PRED_SPIKES_196 = 597,
    PRED_SPIKES_197 = 598,
    PRED_SPIKES_198 = 599,
    PRED_SPIKES_199 = 600,
    PRED_SPIKES_200 = 601,
    PRED_SPIKES_201 = 602,
    PRED_SPIKES_202 = 603,
    PRED_SPIKES_203 = 604,
    PRED_SPIKES_204 = 605,
    PRED_SPIKES_205 = 606,
    PRED_SPIKES_206 = 607,
    PRED_SPIKES_207 = 608,
    PRED_SPIKES_208 = 609,
    PRED_SPIKES_209 = 610,
    PRED_SPIKES_210 = 611,
    PRED_SPIKES_211 = 612,
    PRED_SPIKES_212 = 613,
    PRED_SPIKES_213 = 614,
    PRED_SPIKES_214 = 615,
    PRED_SPIKES_215 = 616,
    PRED_SPIKES_216 = 617,
    PRED_SPIKES_217 = 618,
    PRED_SPIKES_218 = 619,
    PRED_SPIKES_219 = 620,
    PRED_SPIKES_220 = 621,
    PRED_SPIKES_221 = 622,
    PRED_SPIKES_222 = 623,
    PRED_SPIKES_223 = 624,
    PRED_SPIKES_224 = 625,
    PRED_SPIKES_225 = 626,
    PRED_SPIKES_226 = 627,
    PRED_SPIKES_227 = 628,
    PRED_SPIKES_228 = 629,
    PRED_SPIKES_229 = 630,
    PRED_SPIKES_230 = 631,
    PRED_SPIKES_231 = 632,
    PRED_SPIKES_232 = 633,
    PRED_SPIKES_233 = 634,
    PRED_SPIKES_234 = 635,
    PRED_SPIKES_235 = 636,
    PRED_SPIKES_236 = 637,
    PRED_SPIKES_237 = 638,
    PRED_SPIKES_238 = 639,
    PRED_SPIKES_239 = 640,
    PRED_SPIKES_240 = 641,
    PRED_SPIKES_241 = 642,
    PRED_SPIKES_242 = 643,
    PRED_SPIKES_243 = 644,
    PRED_SPIKES_244 = 645,
    PRED_SPIKES_245 = 646,
    PRED_SPIKES_246 = 647,
    PRED_SPIKES_247 = 648,
    PRED_SPIKES_248 = 649,
    PRED_SPIKES_249 = 650,
    PRED_SPIKES_250 = 651,
    PRED_SPIKES_251 = 652,
    PRED_SPIKES_252 = 653,
    PRED_SPIKES_253 = 654,
    PRED_SPIKES_254 = 655,
    PRED_SPIKES_255 = 656,
    PRED_SPIKES_256 = 657,
    PRED_SPIKES_257 = 658,
    PRED_SPIKES_258 = 659,
    PRED_SPIKES_259 = 660,
    PRED_SPIKES_260 = 661,
    PRED_SPIKES_261 = 662,
    PRED_SPIKES_262 = 663,
    PRED_SPIKES_263 = 664,
    PRED_SPIKES_264 = 665,
    PRED_SPIKES_265 = 666,
    PRED_SPIKES_266 = 667,
    PRED_SPIKES_267 = 668,
    PRED_SPIKES_268 = 669,
    PRED_SPIKES_269 = 670,
    PRED_SPIKES_270 = 671,
    PRED_SPIKES_271 = 672,
    PRED_SPIKES_272 = 673,
    PRED_SPIKES_273 = 674,
    PRED_SPIKES_274 = 675,
    PRED_SPIKES_275 = 676,
    PRED_SPIKES_276 = 677,
    PRED_SPIKES_277 = 678,
    PRED_SPIKES_278 = 679,
    PRED_SPIKES_279 = 680,
    PRED_SPIKES_280 = 681,
    PRED_SPIKES_281 = 682,
    PRED_SPIKES_282 = 683,
    PRED_SPIKES_283 = 684,
    PRED_SPIKES_284 = 685,
    PRED_SPIKES_285 = 686,
    PRED_SPIKES_286 = 687,
    PRED_SPIKES_287 = 688,
    PRED_SPIKES_288 = 689,
    PRED_SPIKES_289 = 690,
    PRED_SPIKES_290 = 691,
    PRED_SPIKES_291 = 692,
    PRED_SPIKES_292 = 693,
    PRED_SPIKES_293 = 694,
    PRED_SPIKES_294 = 695,
    PRED_SPIKES_295 = 696,
    PRED_SPIKES_296 = 697,
    PRED_SPIKES_297 = 698,
    PRED_SPIKES_298 = 699,
    PRED_SPIKES_299 = 700,
    PRED_SPIKES_300 = 701,
    PRED_SPIKES_301 = 702,
    PRED_SPIKES_302 = 703,
    PRED_SPIKES_303 = 704,
    PRED_SPIKES_304 = 705,
    PRED_SPIKES_305 = 706,
    PRED_SPIKES_306 = 707,
    PRED_SPIKES_307 = 708,
    PRED_SPIKES_308 = 709,
    PRED_SPIKES_309 = 710,
    PRED_SPIKES_310 = 711,
    PRED_SPIKES_311 = 712,
    PRED_SPIKES_312 = 713,
    PRED_SPIKES_313 = 714,
    PRED_SPIKES_314 = 715,
    PRED_SPIKES_315 = 716,
    PRED_SPIKES_316 = 717,
    PRED_SPIKES_317 = 718,
    PRED_SPIKES_318 = 719,
    PRED_SPIKES_319 = 720,
    PRED_SPIKES_320 = 721,
    PRED_SPIKES_321 = 722,
    PRED_SPIKES_322 = 723,
    PRED_SPIKES_323 = 724,
    PRED_SPIKES_324 = 725,
    PRED_SPIKES_325 = 726,
    PRED_SPIKES_326 = 727,
    PRED_SPIKES_327 = 728,
    PRED_SPIKES_328 = 729,
    PRED_SPIKES_329 = 730,
    PRED_SPIKES_330 = 731,
    PRED_SPIKES_331 = 732,
    PRED_SPIKES_332 = 733,
    PRED_SPIKES_333 = 734,
    PRED_SPIKES_334 = 735,
    PRED_SPIKES_335 = 736,
    PRED_SPIKES_336 = 737,
    PRED_SPIKES_337 = 738,
    PRED_SPIKES_338 = 739,
    PRED_SPIKES_339 = 740,
    PRED_SPIKES_340 = 741,
    PRED_SPIKES_341 = 742,
    PRED_SPIKES_342 = 743,
    PRED_SPIKES_343 = 744,
    PRED_SPIKES_344 = 745,
    PRED_SPIKES_345 = 746,
    PRED_SPIKES_346 = 747,
    PRED_SPIKES_347 = 748,
    PRED_SPIKES_348 = 749,
    PRED_SPIKES_349 = 750,
    PRED_SPIKES_350 = 751,
    PRED_SPIKES_351 = 752,
    PRED_SPIKES_352 = 753,
    PRED_SPIKES_353 = 754,
    PRED_SPIKES_354 = 755,
    PRED_SPIKES_355 = 756,
    PRED_SPIKES_356 = 757,
    PRED_SPIKES_357 = 758,
    PRED_SPIKES_358 = 759,
    PRED_SPIKES_359 = 760,
    PRED_SPIKES_360 = 761,
    PRED_SPIKES_361 = 762,
    PRED_SPIKES_362 = 763,
    PRED_SPIKES_363 = 764,
    PRED_SPIKES_364 = 765,
    PRED_SPIKES_365 = 766,
    PRED_SPIKES_366 = 767,
    PRED_SPIKES_367 = 768,
    PRED_SPIKES_368 = 769,
    PRED_SPIKES_369 = 770,
    PRED_SPIKES_370 = 771,
    PRED_SPIKES_371 = 772,
    PRED_SPIKES_372 = 773,
    PRED_SPIKES_373 = 774,
    PRED_SPIKES_374 = 775,
    PRED_SPIKES_375 = 776,
    PRED_SPIKES_376 = 777,
    PRED_SPIKES_377 = 778,
    PRED_SPIKES_378 = 779,
    PRED_SPIKES_379 = 780,
    PRED_SPIKES_380 = 781,
    PRED_SPIKES_381 = 782,
    PRED_SPIKES_382 = 783,
    PRED_SPIKES_383 = 784,
    PRED_SPIKES_384 = 785,
    PRED_SPIKES_385 = 786,
    PRED_SPIKES_386 = 787,
    PRED_SPIKES_387 = 788,
    PRED_SPIKES_388 = 789,
    PRED_SPIKES_389 = 790,
    PRED_SPIKES_390 = 791,
    PRED_SPIKES_391 = 792,
    PRED_SPIKES_392 = 793,
    PRED_SPIKES_393 = 794,
    PRED_SPIKES_394 = 795,
    PRED_SPIKES_395 = 796,
    PRED_SPIKES_396 = 797,
    PRED_SPIKES_397 = 798,
    PRED_SPIKES_398 = 799,
    PRED_SPIKES_399 = 800,
    MAX_SPIKE_RECEPTOR = 801
  };

  enum ContinuousInput
  {
    NUM_CONTINUOUS_INPUT_PORTS = 0
  };

  static const size_t NUM_SPIKE_RECEPTORS = MAX_SPIKE_RECEPTOR - MIN_SPIKE_RECEPTOR;

static std::vector< std::tuple< int, int > > rport_to_nestml_buffer_idx;

  /**
   * Reset state of neuron.
  **/

  void init_state_internal_();

  /**
   * Reset internal buffers of neuron.
  **/
  void init_buffers_() override;

  /**
   * Initialize auxiliary quantities, leave parameters and state untouched.
  **/
  void pre_run_hook() override;

  /**
   * Take neuron through given time interval
  **/
  void update(nest::Time const &, const long, const long) override;

  // The next two classes need to be friends to access the State_ class/member
  friend class nest::DynamicRecordablesMap< state_neuron >;
  friend class nest::DynamicUniversalDataLogger< state_neuron >;
  friend class nest::DataAccessFunctor< state_neuron >;

  /**
   * Free parameters of the neuron.
   *


   *
   * These are the parameters that can be set by the user through @c `node.set()`.
   * They are initialized from the model prototype when the node is created.
   * Parameters do not change during calls to @c update() and are not reset by
   * @c ResetNetwork.
   *
   * @note Parameters_ need neither copy constructor nor @c operator=(), since
   *       all its members are copied properly by the default copy constructor
   *       and assignment operator. Important:
   *       - If Parameters_ contained @c Time members, you need to define the
   *         assignment operator to recalibrate all members of type @c Time . You
   *         may also want to define the assignment operator.
   *       - If Parameters_ contained members that cannot copy themselves, such
   *         as C-style arrays, you need to define the copy constructor and
   *         assignment operator to copy those members.
  **/
  struct Parameters_
  {    
    //!  Gain
    double kp;
    //!  Sign sensitivity of the neuron
    bool pos;
    //!  Base firing rate
    double base_rate;
    //!  Size of the sliding window
    double buffer_size;
    //!  Number of simulation steps (simulation_time/resolution())
    long simulation_steps;
    //!  Population size for sensory feedback
    long N_fbk;
    //!  Population size for sensory prediction
    long N_pred;
    long fbk_bf_size;
    long pred_bf_size;
    double time_wait;
    double time_trial;

    /**
     * Initialize parameters to their default values.
    **/
    Parameters_();
  };

  /**
   * Dynamic state of the neuron.
   *
   *
   *
   * These are the state variables that are advanced in time by calls to
   * @c update(). In many models, some or all of them can be set by the user
   * through @c `node.set()`. The state variables are initialized from the model
   * prototype when the node is created. State variables are reset by @c ResetNetwork.
   *
   * @note State_ need neither copy constructor nor @c operator=(), since
   *       all its members are copied properly by the default copy constructor
   *       and assignment operator. Important:
   *       - If State_ contained @c Time members, you need to define the
   *         assignment operator to recalibrate all members of type @c Time . You
   *         may also want to define the assignment operator.
   *       - If State_ contained members that cannot copy themselves, such
   *         as C-style arrays, you need to define the copy constructor and
   *         assignment operator to copy those members.
  **/
  struct State_
  {
enum StateVecVars {
    IN_RATE = 0,
    OUT_RATE = 1,
    CURRENT_FBK_INPUT = 2,
    CURRENT_PRED_INPUT = 402,
    FBK_BUFFER = 802,
    PRED_BUFFER = 10802,
    FBK_COUNTS = 20802,
    PRED_COUNTS = 21202,
    MEAN_FBK = 21602,
    MEAN_PRED = 21603,
    VAR_FBK = 21604,
    VAR_PRED = 21605,
    CV_FBK = 21606,
    CV_PRED = 21607,
    TOTAL_CV = 21608,
    LAMBDA_POISSON = 21609,
};    
    //!  Input firing rate: to be computed from spikes
    double in_rate;
    //!  Output firing rate: defined accordingly to the input firing rate
    double out_rate;
    //!  Outgoing spikes
    long spike_count_out;
    std::vector< double >  current_fbk_input;
    std::vector< double >  current_pred_input;
    //!  Buffer for sensory feedback spikes
    std::vector< double >  fbk_buffer;
    //!  Buffer for sensory prediction spikes
    std::vector< double >  pred_buffer;
    //!  Counts of incoming feedback spikes
    std::vector< double >  fbk_counts;
    //!  Counts of incoming prediction spikes
    std::vector< double >  pred_counts;
    //!  Tick 
    long tick;
    long position_count;
    //!  Mean sensory feedback
    double mean_fbk;
    //!  Mean sensory prediction
    double mean_pred;
    //!  Variance of sensory feedback
    double var_fbk;
    //!  Variance of sensory prediction
    double var_pred;
    //!  Coefficient of variation of sensory feedback
    double CV_fbk;
    //!  Coefficient of variation of sensory prediction
    double CV_pred;
    double total_CV;
    //!  Parameter of the Poisson distribution defining generator behavior
    double lambda_poisson;

    State_();
  };

  struct DelayedVariables_
  {
  };

  /**
   * Internal variables of the neuron.
   *
   *
   *
   * These variables must be initialized by @c pre_run_hook (or calibrate in NEST 3.3 and older), which is called before
   * the first call to @c update() upon each call to @c Simulate.
   * @node Variables_ needs neither constructor, copy constructor or assignment operator,
   *       since it is initialized by @c pre_run_hook() (or calibrate() in NEST 3.3 and older). If Variables_ has members that
   *       cannot destroy themselves, Variables_ will need a destructor.
  **/
  struct Variables_
  {
    double res;
    double __h;
    long buffer_steps;
    long trial_steps;
    long wait_steps;
  };

  /**
   * Buffers of the neuron.
   * Usually buffers for incoming spikes and data logged for analog recorders.
   * Buffers must be initialized by @c init_buffers_(), which is called before
   * @c pre_run_hook() (or calibrate() in NEST 3.3 and older) on the first call to @c Simulate after the start of NEST,
   * ResetKernel or ResetNetwork.
   * @node Buffers_ needs neither constructor, copy constructor or assignment operator,
   *       since it is initialized by @c init_nodes_(). If Buffers_ has members that
   *       cannot destroy themselves, Buffers_ will need a destructor.
  **/
  struct Buffers_
  {
    Buffers_(state_neuron &);
    Buffers_(const Buffers_ &, state_neuron &);

    /**
     * Logger for all analog data
    **/
    nest::DynamicUniversalDataLogger<state_neuron> logger_;

    // -----------------------------------------------------------------------
    //   Spike buffers and sums of incoming spikes/currents per timestep
    // -----------------------------------------------------------------------    



    /**
     * Buffer containing the incoming spikes
    **/
    inline std::vector< nest::RingBuffer >& get_spike_inputs_()
    {
        return spike_inputs_;
    }
    std::vector< nest::RingBuffer > spike_inputs_;

    /**
     * Buffer containing the sum of all the incoming spikes
    **/
    inline std::vector< double >& get_spike_inputs_grid_sum_()
    {
        return spike_inputs_grid_sum_;
    }
    std::vector< double > spike_inputs_grid_sum_;

    /**
     * Buffer containing a flag whether incoming spikes have been received on a given port
    **/
    inline std::vector< nest::RingBuffer >& get_spike_input_received_()
    {
        return spike_input_received_;
    }
    std::vector< nest::RingBuffer > spike_input_received_;

    /**
     * Buffer containing a flag whether incoming spikes have been received on a given port
    **/
    inline std::vector< double >& get_spike_input_received_grid_sum_()
    {
        return spike_input_received_grid_sum_;
    }
    std::vector< double > spike_input_received_grid_sum_;

    // -----------------------------------------------------------------------
    //   Continuous-input buffers
    // -----------------------------------------------------------------------

    




    /**
     * Buffer containing the incoming continuous input
    **/
    inline std::vector< nest::RingBuffer >& get_continuous_inputs_()
    {
        return continuous_inputs_;
    }
    std::vector< nest::RingBuffer > continuous_inputs_;

    /**
     * Buffer containing the sum of all the continuous inputs
    **/
    inline std::vector< double >& get_continuous_inputs_grid_sum_()
    {
        return continuous_inputs_grid_sum_;
    }
    std::vector< double > continuous_inputs_grid_sum_;
  };

  // -------------------------------------------------------------------------
  //   Getters/setters for inline expressions
  // -------------------------------------------------------------------------

  

  // -------------------------------------------------------------------------
  //   Getters/setters for input buffers
  // -------------------------------------------------------------------------  




  /**
   * Buffer containing the incoming spikes
  **/
  inline std::vector< nest::RingBuffer >& get_spike_inputs_()
  {
      return B_.get_spike_inputs_();
  }

  /**
   * Buffer containing the sum of all the incoming spikes
  **/
  inline std::vector< double >& get_spike_inputs_grid_sum_()
  {
      return B_.get_spike_inputs_grid_sum_();
  }

  /**
   * Buffer containing a flag whether incoming spikes have been received on a given port
  **/
  inline std::vector< nest::RingBuffer >& get_spike_input_received_()
  {
      return B_.get_spike_input_received_();
  }

  /**
   * Buffer containing a flag whether incoming spikes have been received on a given port
  **/
  inline std::vector< double >& get_spike_input_received_grid_sum_()
  {
      return B_.get_spike_input_received_grid_sum_();
  }




  /**
   * Buffer containing the incoming continuous input
  **/
  inline std::vector< nest::RingBuffer >& get_continuous_inputs_()
  {
      return B_.get_continuous_inputs_();
  }

  /**
   * Buffer containing the sum of all the continuous inputs
  **/
  inline std::vector< double >& get_continuous_inputs_grid_sum_()
  {
      return B_.get_continuous_inputs_grid_sum_();
  }

  // -------------------------------------------------------------------------
  //   Member variables of neuron model.
  //   Each model neuron should have precisely the following four data members,
  //   which are one instance each of the parameters, state, buffers and variables
  //   structures. Experience indicates that the state and variables member should
  //   be next to each other to achieve good efficiency (caching).
  //   Note: Devices require one additional data member, an instance of the
  //   ``Device`` child class they belong to.
  // -------------------------------------------------------------------------


  Parameters_       P_;        //!< Free parameters.
  State_            S_;        //!< Dynamic state.
  DelayedVariables_ DV_;       //!< Delayed state variables.
  Variables_        V_;        //!< Internal Variables
  Buffers_          B_;        //!< Buffers.

  //! Mapping of recordables names to access functions
  nest::DynamicRecordablesMap<state_neuron> recordablesMap_;
  nest::DataAccessFunctor< state_neuron > get_data_access_functor( size_t elem );
  std::string get_var_name(size_t elem, std::string var_name);
  void insert_recordables(size_t first=0);


inline double get_state_element(size_t elem)
  {
    if
    (elem == State_::IN_RATE)
    {
      return S_.in_rate;
    }
    else if
    (elem == State_::OUT_RATE)
    {
      return S_.out_rate;
    }
    else if(elem >= State_::CURRENT_FBK_INPUT and elem < State_::CURRENT_FBK_INPUT + 
P_.N_fbk)
    {
      return S_.current_fbk_input[ elem - State_::CURRENT_FBK_INPUT ];
    }
    else if(elem >= State_::CURRENT_PRED_INPUT and elem < State_::CURRENT_PRED_INPUT + 
P_.N_pred)
    {
      return S_.current_pred_input[ elem - State_::CURRENT_PRED_INPUT ];
    }
    else if(elem >= State_::FBK_BUFFER and elem < State_::FBK_BUFFER + 
P_.fbk_bf_size)
    {
      return S_.fbk_buffer[ elem - State_::FBK_BUFFER ];
    }
    else if(elem >= State_::PRED_BUFFER and elem < State_::PRED_BUFFER + 
P_.pred_bf_size)
    {
      return S_.pred_buffer[ elem - State_::PRED_BUFFER ];
    }
    else if(elem >= State_::FBK_COUNTS and elem < State_::FBK_COUNTS + 
P_.N_fbk)
    {
      return S_.fbk_counts[ elem - State_::FBK_COUNTS ];
    }
    else if(elem >= State_::PRED_COUNTS and elem < State_::PRED_COUNTS + 
P_.N_pred)
    {
      return S_.pred_counts[ elem - State_::PRED_COUNTS ];
    }
    else if
    (elem == State_::MEAN_FBK)
    {
      return S_.mean_fbk;
    }
    else if
    (elem == State_::MEAN_PRED)
    {
      return S_.mean_pred;
    }
    else if
    (elem == State_::VAR_FBK)
    {
      return S_.var_fbk;
    }
    else if
    (elem == State_::VAR_PRED)
    {
      return S_.var_pred;
    }
    else if
    (elem == State_::CV_FBK)
    {
      return S_.CV_fbk;
    }
    else if
    (elem == State_::CV_PRED)
    {
      return S_.CV_pred;
    }
    else if
    (elem == State_::TOTAL_CV)
    {
      return S_.total_CV;
    }
    else
    {
      return S_.lambda_poisson;
    }
  }
  nest::normal_distribution normal_dev_; //!< random deviate generator
  nest::poisson_distribution poisson_dev_; //!< random deviate generator

}; /* neuron state_neuron */

inline nest_port_t state_neuron::send_test_event(nest::Node& target, nest_rport_t receptor_type, nest::synindex, bool)
{
  // You should usually not change the code in this function.
  // It confirms that the target of connection @c c accepts @c nest::SpikeEvent on
  // the given @c receptor_type.
  nest::SpikeEvent e;
  e.set_sender(*this);
  return target.handles_test_event(e, receptor_type);
}

inline nest_port_t state_neuron::handles_test_event(nest::SpikeEvent&, nest_port_t receptor_type)
{
    assert( B_.spike_inputs_.size() == NUM_SPIKE_RECEPTORS );
    if ( receptor_type < MIN_SPIKE_RECEPTOR or receptor_type >= MAX_SPIKE_RECEPTOR )
    {
      throw nest::UnknownReceptorType( receptor_type, get_name() );
    }
    return receptor_type - MIN_SPIKE_RECEPTOR;
}

inline nest_port_t state_neuron::handles_test_event(nest::DataLoggingRequest& dlr, nest_port_t receptor_type)
{
  // You should usually not change the code in this function.
  // It confirms to the connection management system that we are able
  // to handle @c DataLoggingRequest on port 0.
  // The function also tells the built-in UniversalDataLogger that this node
  // is recorded from and that it thus needs to collect data during simulation.
  if (receptor_type != 0)
  {
    throw nest::UnknownReceptorType(receptor_type, get_name());
  }

  return B_.logger_.connect_logging_device(dlr, recordablesMap_);
}

inline void state_neuron::get_status(DictionaryDatum &__d) const
{
  // parameters
  def< double >(__d, nest::state_neuron_names::_kp, get_kp());
  def< bool >(__d, nest::state_neuron_names::_pos, get_pos());
  def< double >(__d, nest::state_neuron_names::_base_rate, get_base_rate());
  def< double >(__d, nest::state_neuron_names::_buffer_size, get_buffer_size());
  def< long >(__d, nest::state_neuron_names::_simulation_steps, get_simulation_steps());
  def< long >(__d, nest::state_neuron_names::_N_fbk, get_N_fbk());
  def< long >(__d, nest::state_neuron_names::_N_pred, get_N_pred());
  def< long >(__d, nest::state_neuron_names::_fbk_bf_size, get_fbk_bf_size());
  def< long >(__d, nest::state_neuron_names::_pred_bf_size, get_pred_bf_size());
  def< double >(__d, nest::state_neuron_names::_time_wait, get_time_wait());
  def< double >(__d, nest::state_neuron_names::_time_trial, get_time_trial());

  // initial values for state variables in ODE or kernel
  def< double >(__d, nest::state_neuron_names::_in_rate, get_in_rate());
  def< double >(__d, nest::state_neuron_names::_out_rate, get_out_rate());
  def< long >(__d, nest::state_neuron_names::_spike_count_out, get_spike_count_out());
  def< std::vector< double >  >(__d, nest::state_neuron_names::_current_fbk_input, get_current_fbk_input());
  def< std::vector< double >  >(__d, nest::state_neuron_names::_current_pred_input, get_current_pred_input());
  def< std::vector< double >  >(__d, nest::state_neuron_names::_fbk_buffer, get_fbk_buffer());
  def< std::vector< double >  >(__d, nest::state_neuron_names::_pred_buffer, get_pred_buffer());
  def< std::vector< double >  >(__d, nest::state_neuron_names::_fbk_counts, get_fbk_counts());
  def< std::vector< double >  >(__d, nest::state_neuron_names::_pred_counts, get_pred_counts());
  def< long >(__d, nest::state_neuron_names::_tick, get_tick());
  def< long >(__d, nest::state_neuron_names::_position_count, get_position_count());
  def< double >(__d, nest::state_neuron_names::_mean_fbk, get_mean_fbk());
  def< double >(__d, nest::state_neuron_names::_mean_pred, get_mean_pred());
  def< double >(__d, nest::state_neuron_names::_var_fbk, get_var_fbk());
  def< double >(__d, nest::state_neuron_names::_var_pred, get_var_pred());
  def< double >(__d, nest::state_neuron_names::_CV_fbk, get_CV_fbk());
  def< double >(__d, nest::state_neuron_names::_CV_pred, get_CV_pred());
  def< double >(__d, nest::state_neuron_names::_total_CV, get_total_CV());
  def< double >(__d, nest::state_neuron_names::_lambda_poisson, get_lambda_poisson());

  ArchivingNode::get_status( __d );
  DictionaryDatum __receptor_type = new Dictionary();
    ( *__receptor_type )[ "FBK_SPIKES_0" ] = 1,
    ( *__receptor_type )[ "FBK_SPIKES_1" ] = 2,
    ( *__receptor_type )[ "FBK_SPIKES_2" ] = 3,
    ( *__receptor_type )[ "FBK_SPIKES_3" ] = 4,
    ( *__receptor_type )[ "FBK_SPIKES_4" ] = 5,
    ( *__receptor_type )[ "FBK_SPIKES_5" ] = 6,
    ( *__receptor_type )[ "FBK_SPIKES_6" ] = 7,
    ( *__receptor_type )[ "FBK_SPIKES_7" ] = 8,
    ( *__receptor_type )[ "FBK_SPIKES_8" ] = 9,
    ( *__receptor_type )[ "FBK_SPIKES_9" ] = 10,
    ( *__receptor_type )[ "FBK_SPIKES_10" ] = 11,
    ( *__receptor_type )[ "FBK_SPIKES_11" ] = 12,
    ( *__receptor_type )[ "FBK_SPIKES_12" ] = 13,
    ( *__receptor_type )[ "FBK_SPIKES_13" ] = 14,
    ( *__receptor_type )[ "FBK_SPIKES_14" ] = 15,
    ( *__receptor_type )[ "FBK_SPIKES_15" ] = 16,
    ( *__receptor_type )[ "FBK_SPIKES_16" ] = 17,
    ( *__receptor_type )[ "FBK_SPIKES_17" ] = 18,
    ( *__receptor_type )[ "FBK_SPIKES_18" ] = 19,
    ( *__receptor_type )[ "FBK_SPIKES_19" ] = 20,
    ( *__receptor_type )[ "FBK_SPIKES_20" ] = 21,
    ( *__receptor_type )[ "FBK_SPIKES_21" ] = 22,
    ( *__receptor_type )[ "FBK_SPIKES_22" ] = 23,
    ( *__receptor_type )[ "FBK_SPIKES_23" ] = 24,
    ( *__receptor_type )[ "FBK_SPIKES_24" ] = 25,
    ( *__receptor_type )[ "FBK_SPIKES_25" ] = 26,
    ( *__receptor_type )[ "FBK_SPIKES_26" ] = 27,
    ( *__receptor_type )[ "FBK_SPIKES_27" ] = 28,
    ( *__receptor_type )[ "FBK_SPIKES_28" ] = 29,
    ( *__receptor_type )[ "FBK_SPIKES_29" ] = 30,
    ( *__receptor_type )[ "FBK_SPIKES_30" ] = 31,
    ( *__receptor_type )[ "FBK_SPIKES_31" ] = 32,
    ( *__receptor_type )[ "FBK_SPIKES_32" ] = 33,
    ( *__receptor_type )[ "FBK_SPIKES_33" ] = 34,
    ( *__receptor_type )[ "FBK_SPIKES_34" ] = 35,
    ( *__receptor_type )[ "FBK_SPIKES_35" ] = 36,
    ( *__receptor_type )[ "FBK_SPIKES_36" ] = 37,
    ( *__receptor_type )[ "FBK_SPIKES_37" ] = 38,
    ( *__receptor_type )[ "FBK_SPIKES_38" ] = 39,
    ( *__receptor_type )[ "FBK_SPIKES_39" ] = 40,
    ( *__receptor_type )[ "FBK_SPIKES_40" ] = 41,
    ( *__receptor_type )[ "FBK_SPIKES_41" ] = 42,
    ( *__receptor_type )[ "FBK_SPIKES_42" ] = 43,
    ( *__receptor_type )[ "FBK_SPIKES_43" ] = 44,
    ( *__receptor_type )[ "FBK_SPIKES_44" ] = 45,
    ( *__receptor_type )[ "FBK_SPIKES_45" ] = 46,
    ( *__receptor_type )[ "FBK_SPIKES_46" ] = 47,
    ( *__receptor_type )[ "FBK_SPIKES_47" ] = 48,
    ( *__receptor_type )[ "FBK_SPIKES_48" ] = 49,
    ( *__receptor_type )[ "FBK_SPIKES_49" ] = 50,
    ( *__receptor_type )[ "FBK_SPIKES_50" ] = 51,
    ( *__receptor_type )[ "FBK_SPIKES_51" ] = 52,
    ( *__receptor_type )[ "FBK_SPIKES_52" ] = 53,
    ( *__receptor_type )[ "FBK_SPIKES_53" ] = 54,
    ( *__receptor_type )[ "FBK_SPIKES_54" ] = 55,
    ( *__receptor_type )[ "FBK_SPIKES_55" ] = 56,
    ( *__receptor_type )[ "FBK_SPIKES_56" ] = 57,
    ( *__receptor_type )[ "FBK_SPIKES_57" ] = 58,
    ( *__receptor_type )[ "FBK_SPIKES_58" ] = 59,
    ( *__receptor_type )[ "FBK_SPIKES_59" ] = 60,
    ( *__receptor_type )[ "FBK_SPIKES_60" ] = 61,
    ( *__receptor_type )[ "FBK_SPIKES_61" ] = 62,
    ( *__receptor_type )[ "FBK_SPIKES_62" ] = 63,
    ( *__receptor_type )[ "FBK_SPIKES_63" ] = 64,
    ( *__receptor_type )[ "FBK_SPIKES_64" ] = 65,
    ( *__receptor_type )[ "FBK_SPIKES_65" ] = 66,
    ( *__receptor_type )[ "FBK_SPIKES_66" ] = 67,
    ( *__receptor_type )[ "FBK_SPIKES_67" ] = 68,
    ( *__receptor_type )[ "FBK_SPIKES_68" ] = 69,
    ( *__receptor_type )[ "FBK_SPIKES_69" ] = 70,
    ( *__receptor_type )[ "FBK_SPIKES_70" ] = 71,
    ( *__receptor_type )[ "FBK_SPIKES_71" ] = 72,
    ( *__receptor_type )[ "FBK_SPIKES_72" ] = 73,
    ( *__receptor_type )[ "FBK_SPIKES_73" ] = 74,
    ( *__receptor_type )[ "FBK_SPIKES_74" ] = 75,
    ( *__receptor_type )[ "FBK_SPIKES_75" ] = 76,
    ( *__receptor_type )[ "FBK_SPIKES_76" ] = 77,
    ( *__receptor_type )[ "FBK_SPIKES_77" ] = 78,
    ( *__receptor_type )[ "FBK_SPIKES_78" ] = 79,
    ( *__receptor_type )[ "FBK_SPIKES_79" ] = 80,
    ( *__receptor_type )[ "FBK_SPIKES_80" ] = 81,
    ( *__receptor_type )[ "FBK_SPIKES_81" ] = 82,
    ( *__receptor_type )[ "FBK_SPIKES_82" ] = 83,
    ( *__receptor_type )[ "FBK_SPIKES_83" ] = 84,
    ( *__receptor_type )[ "FBK_SPIKES_84" ] = 85,
    ( *__receptor_type )[ "FBK_SPIKES_85" ] = 86,
    ( *__receptor_type )[ "FBK_SPIKES_86" ] = 87,
    ( *__receptor_type )[ "FBK_SPIKES_87" ] = 88,
    ( *__receptor_type )[ "FBK_SPIKES_88" ] = 89,
    ( *__receptor_type )[ "FBK_SPIKES_89" ] = 90,
    ( *__receptor_type )[ "FBK_SPIKES_90" ] = 91,
    ( *__receptor_type )[ "FBK_SPIKES_91" ] = 92,
    ( *__receptor_type )[ "FBK_SPIKES_92" ] = 93,
    ( *__receptor_type )[ "FBK_SPIKES_93" ] = 94,
    ( *__receptor_type )[ "FBK_SPIKES_94" ] = 95,
    ( *__receptor_type )[ "FBK_SPIKES_95" ] = 96,
    ( *__receptor_type )[ "FBK_SPIKES_96" ] = 97,
    ( *__receptor_type )[ "FBK_SPIKES_97" ] = 98,
    ( *__receptor_type )[ "FBK_SPIKES_98" ] = 99,
    ( *__receptor_type )[ "FBK_SPIKES_99" ] = 100,
    ( *__receptor_type )[ "FBK_SPIKES_100" ] = 101,
    ( *__receptor_type )[ "FBK_SPIKES_101" ] = 102,
    ( *__receptor_type )[ "FBK_SPIKES_102" ] = 103,
    ( *__receptor_type )[ "FBK_SPIKES_103" ] = 104,
    ( *__receptor_type )[ "FBK_SPIKES_104" ] = 105,
    ( *__receptor_type )[ "FBK_SPIKES_105" ] = 106,
    ( *__receptor_type )[ "FBK_SPIKES_106" ] = 107,
    ( *__receptor_type )[ "FBK_SPIKES_107" ] = 108,
    ( *__receptor_type )[ "FBK_SPIKES_108" ] = 109,
    ( *__receptor_type )[ "FBK_SPIKES_109" ] = 110,
    ( *__receptor_type )[ "FBK_SPIKES_110" ] = 111,
    ( *__receptor_type )[ "FBK_SPIKES_111" ] = 112,
    ( *__receptor_type )[ "FBK_SPIKES_112" ] = 113,
    ( *__receptor_type )[ "FBK_SPIKES_113" ] = 114,
    ( *__receptor_type )[ "FBK_SPIKES_114" ] = 115,
    ( *__receptor_type )[ "FBK_SPIKES_115" ] = 116,
    ( *__receptor_type )[ "FBK_SPIKES_116" ] = 117,
    ( *__receptor_type )[ "FBK_SPIKES_117" ] = 118,
    ( *__receptor_type )[ "FBK_SPIKES_118" ] = 119,
    ( *__receptor_type )[ "FBK_SPIKES_119" ] = 120,
    ( *__receptor_type )[ "FBK_SPIKES_120" ] = 121,
    ( *__receptor_type )[ "FBK_SPIKES_121" ] = 122,
    ( *__receptor_type )[ "FBK_SPIKES_122" ] = 123,
    ( *__receptor_type )[ "FBK_SPIKES_123" ] = 124,
    ( *__receptor_type )[ "FBK_SPIKES_124" ] = 125,
    ( *__receptor_type )[ "FBK_SPIKES_125" ] = 126,
    ( *__receptor_type )[ "FBK_SPIKES_126" ] = 127,
    ( *__receptor_type )[ "FBK_SPIKES_127" ] = 128,
    ( *__receptor_type )[ "FBK_SPIKES_128" ] = 129,
    ( *__receptor_type )[ "FBK_SPIKES_129" ] = 130,
    ( *__receptor_type )[ "FBK_SPIKES_130" ] = 131,
    ( *__receptor_type )[ "FBK_SPIKES_131" ] = 132,
    ( *__receptor_type )[ "FBK_SPIKES_132" ] = 133,
    ( *__receptor_type )[ "FBK_SPIKES_133" ] = 134,
    ( *__receptor_type )[ "FBK_SPIKES_134" ] = 135,
    ( *__receptor_type )[ "FBK_SPIKES_135" ] = 136,
    ( *__receptor_type )[ "FBK_SPIKES_136" ] = 137,
    ( *__receptor_type )[ "FBK_SPIKES_137" ] = 138,
    ( *__receptor_type )[ "FBK_SPIKES_138" ] = 139,
    ( *__receptor_type )[ "FBK_SPIKES_139" ] = 140,
    ( *__receptor_type )[ "FBK_SPIKES_140" ] = 141,
    ( *__receptor_type )[ "FBK_SPIKES_141" ] = 142,
    ( *__receptor_type )[ "FBK_SPIKES_142" ] = 143,
    ( *__receptor_type )[ "FBK_SPIKES_143" ] = 144,
    ( *__receptor_type )[ "FBK_SPIKES_144" ] = 145,
    ( *__receptor_type )[ "FBK_SPIKES_145" ] = 146,
    ( *__receptor_type )[ "FBK_SPIKES_146" ] = 147,
    ( *__receptor_type )[ "FBK_SPIKES_147" ] = 148,
    ( *__receptor_type )[ "FBK_SPIKES_148" ] = 149,
    ( *__receptor_type )[ "FBK_SPIKES_149" ] = 150,
    ( *__receptor_type )[ "FBK_SPIKES_150" ] = 151,
    ( *__receptor_type )[ "FBK_SPIKES_151" ] = 152,
    ( *__receptor_type )[ "FBK_SPIKES_152" ] = 153,
    ( *__receptor_type )[ "FBK_SPIKES_153" ] = 154,
    ( *__receptor_type )[ "FBK_SPIKES_154" ] = 155,
    ( *__receptor_type )[ "FBK_SPIKES_155" ] = 156,
    ( *__receptor_type )[ "FBK_SPIKES_156" ] = 157,
    ( *__receptor_type )[ "FBK_SPIKES_157" ] = 158,
    ( *__receptor_type )[ "FBK_SPIKES_158" ] = 159,
    ( *__receptor_type )[ "FBK_SPIKES_159" ] = 160,
    ( *__receptor_type )[ "FBK_SPIKES_160" ] = 161,
    ( *__receptor_type )[ "FBK_SPIKES_161" ] = 162,
    ( *__receptor_type )[ "FBK_SPIKES_162" ] = 163,
    ( *__receptor_type )[ "FBK_SPIKES_163" ] = 164,
    ( *__receptor_type )[ "FBK_SPIKES_164" ] = 165,
    ( *__receptor_type )[ "FBK_SPIKES_165" ] = 166,
    ( *__receptor_type )[ "FBK_SPIKES_166" ] = 167,
    ( *__receptor_type )[ "FBK_SPIKES_167" ] = 168,
    ( *__receptor_type )[ "FBK_SPIKES_168" ] = 169,
    ( *__receptor_type )[ "FBK_SPIKES_169" ] = 170,
    ( *__receptor_type )[ "FBK_SPIKES_170" ] = 171,
    ( *__receptor_type )[ "FBK_SPIKES_171" ] = 172,
    ( *__receptor_type )[ "FBK_SPIKES_172" ] = 173,
    ( *__receptor_type )[ "FBK_SPIKES_173" ] = 174,
    ( *__receptor_type )[ "FBK_SPIKES_174" ] = 175,
    ( *__receptor_type )[ "FBK_SPIKES_175" ] = 176,
    ( *__receptor_type )[ "FBK_SPIKES_176" ] = 177,
    ( *__receptor_type )[ "FBK_SPIKES_177" ] = 178,
    ( *__receptor_type )[ "FBK_SPIKES_178" ] = 179,
    ( *__receptor_type )[ "FBK_SPIKES_179" ] = 180,
    ( *__receptor_type )[ "FBK_SPIKES_180" ] = 181,
    ( *__receptor_type )[ "FBK_SPIKES_181" ] = 182,
    ( *__receptor_type )[ "FBK_SPIKES_182" ] = 183,
    ( *__receptor_type )[ "FBK_SPIKES_183" ] = 184,
    ( *__receptor_type )[ "FBK_SPIKES_184" ] = 185,
    ( *__receptor_type )[ "FBK_SPIKES_185" ] = 186,
    ( *__receptor_type )[ "FBK_SPIKES_186" ] = 187,
    ( *__receptor_type )[ "FBK_SPIKES_187" ] = 188,
    ( *__receptor_type )[ "FBK_SPIKES_188" ] = 189,
    ( *__receptor_type )[ "FBK_SPIKES_189" ] = 190,
    ( *__receptor_type )[ "FBK_SPIKES_190" ] = 191,
    ( *__receptor_type )[ "FBK_SPIKES_191" ] = 192,
    ( *__receptor_type )[ "FBK_SPIKES_192" ] = 193,
    ( *__receptor_type )[ "FBK_SPIKES_193" ] = 194,
    ( *__receptor_type )[ "FBK_SPIKES_194" ] = 195,
    ( *__receptor_type )[ "FBK_SPIKES_195" ] = 196,
    ( *__receptor_type )[ "FBK_SPIKES_196" ] = 197,
    ( *__receptor_type )[ "FBK_SPIKES_197" ] = 198,
    ( *__receptor_type )[ "FBK_SPIKES_198" ] = 199,
    ( *__receptor_type )[ "FBK_SPIKES_199" ] = 200,
    ( *__receptor_type )[ "FBK_SPIKES_200" ] = 201,
    ( *__receptor_type )[ "FBK_SPIKES_201" ] = 202,
    ( *__receptor_type )[ "FBK_SPIKES_202" ] = 203,
    ( *__receptor_type )[ "FBK_SPIKES_203" ] = 204,
    ( *__receptor_type )[ "FBK_SPIKES_204" ] = 205,
    ( *__receptor_type )[ "FBK_SPIKES_205" ] = 206,
    ( *__receptor_type )[ "FBK_SPIKES_206" ] = 207,
    ( *__receptor_type )[ "FBK_SPIKES_207" ] = 208,
    ( *__receptor_type )[ "FBK_SPIKES_208" ] = 209,
    ( *__receptor_type )[ "FBK_SPIKES_209" ] = 210,
    ( *__receptor_type )[ "FBK_SPIKES_210" ] = 211,
    ( *__receptor_type )[ "FBK_SPIKES_211" ] = 212,
    ( *__receptor_type )[ "FBK_SPIKES_212" ] = 213,
    ( *__receptor_type )[ "FBK_SPIKES_213" ] = 214,
    ( *__receptor_type )[ "FBK_SPIKES_214" ] = 215,
    ( *__receptor_type )[ "FBK_SPIKES_215" ] = 216,
    ( *__receptor_type )[ "FBK_SPIKES_216" ] = 217,
    ( *__receptor_type )[ "FBK_SPIKES_217" ] = 218,
    ( *__receptor_type )[ "FBK_SPIKES_218" ] = 219,
    ( *__receptor_type )[ "FBK_SPIKES_219" ] = 220,
    ( *__receptor_type )[ "FBK_SPIKES_220" ] = 221,
    ( *__receptor_type )[ "FBK_SPIKES_221" ] = 222,
    ( *__receptor_type )[ "FBK_SPIKES_222" ] = 223,
    ( *__receptor_type )[ "FBK_SPIKES_223" ] = 224,
    ( *__receptor_type )[ "FBK_SPIKES_224" ] = 225,
    ( *__receptor_type )[ "FBK_SPIKES_225" ] = 226,
    ( *__receptor_type )[ "FBK_SPIKES_226" ] = 227,
    ( *__receptor_type )[ "FBK_SPIKES_227" ] = 228,
    ( *__receptor_type )[ "FBK_SPIKES_228" ] = 229,
    ( *__receptor_type )[ "FBK_SPIKES_229" ] = 230,
    ( *__receptor_type )[ "FBK_SPIKES_230" ] = 231,
    ( *__receptor_type )[ "FBK_SPIKES_231" ] = 232,
    ( *__receptor_type )[ "FBK_SPIKES_232" ] = 233,
    ( *__receptor_type )[ "FBK_SPIKES_233" ] = 234,
    ( *__receptor_type )[ "FBK_SPIKES_234" ] = 235,
    ( *__receptor_type )[ "FBK_SPIKES_235" ] = 236,
    ( *__receptor_type )[ "FBK_SPIKES_236" ] = 237,
    ( *__receptor_type )[ "FBK_SPIKES_237" ] = 238,
    ( *__receptor_type )[ "FBK_SPIKES_238" ] = 239,
    ( *__receptor_type )[ "FBK_SPIKES_239" ] = 240,
    ( *__receptor_type )[ "FBK_SPIKES_240" ] = 241,
    ( *__receptor_type )[ "FBK_SPIKES_241" ] = 242,
    ( *__receptor_type )[ "FBK_SPIKES_242" ] = 243,
    ( *__receptor_type )[ "FBK_SPIKES_243" ] = 244,
    ( *__receptor_type )[ "FBK_SPIKES_244" ] = 245,
    ( *__receptor_type )[ "FBK_SPIKES_245" ] = 246,
    ( *__receptor_type )[ "FBK_SPIKES_246" ] = 247,
    ( *__receptor_type )[ "FBK_SPIKES_247" ] = 248,
    ( *__receptor_type )[ "FBK_SPIKES_248" ] = 249,
    ( *__receptor_type )[ "FBK_SPIKES_249" ] = 250,
    ( *__receptor_type )[ "FBK_SPIKES_250" ] = 251,
    ( *__receptor_type )[ "FBK_SPIKES_251" ] = 252,
    ( *__receptor_type )[ "FBK_SPIKES_252" ] = 253,
    ( *__receptor_type )[ "FBK_SPIKES_253" ] = 254,
    ( *__receptor_type )[ "FBK_SPIKES_254" ] = 255,
    ( *__receptor_type )[ "FBK_SPIKES_255" ] = 256,
    ( *__receptor_type )[ "FBK_SPIKES_256" ] = 257,
    ( *__receptor_type )[ "FBK_SPIKES_257" ] = 258,
    ( *__receptor_type )[ "FBK_SPIKES_258" ] = 259,
    ( *__receptor_type )[ "FBK_SPIKES_259" ] = 260,
    ( *__receptor_type )[ "FBK_SPIKES_260" ] = 261,
    ( *__receptor_type )[ "FBK_SPIKES_261" ] = 262,
    ( *__receptor_type )[ "FBK_SPIKES_262" ] = 263,
    ( *__receptor_type )[ "FBK_SPIKES_263" ] = 264,
    ( *__receptor_type )[ "FBK_SPIKES_264" ] = 265,
    ( *__receptor_type )[ "FBK_SPIKES_265" ] = 266,
    ( *__receptor_type )[ "FBK_SPIKES_266" ] = 267,
    ( *__receptor_type )[ "FBK_SPIKES_267" ] = 268,
    ( *__receptor_type )[ "FBK_SPIKES_268" ] = 269,
    ( *__receptor_type )[ "FBK_SPIKES_269" ] = 270,
    ( *__receptor_type )[ "FBK_SPIKES_270" ] = 271,
    ( *__receptor_type )[ "FBK_SPIKES_271" ] = 272,
    ( *__receptor_type )[ "FBK_SPIKES_272" ] = 273,
    ( *__receptor_type )[ "FBK_SPIKES_273" ] = 274,
    ( *__receptor_type )[ "FBK_SPIKES_274" ] = 275,
    ( *__receptor_type )[ "FBK_SPIKES_275" ] = 276,
    ( *__receptor_type )[ "FBK_SPIKES_276" ] = 277,
    ( *__receptor_type )[ "FBK_SPIKES_277" ] = 278,
    ( *__receptor_type )[ "FBK_SPIKES_278" ] = 279,
    ( *__receptor_type )[ "FBK_SPIKES_279" ] = 280,
    ( *__receptor_type )[ "FBK_SPIKES_280" ] = 281,
    ( *__receptor_type )[ "FBK_SPIKES_281" ] = 282,
    ( *__receptor_type )[ "FBK_SPIKES_282" ] = 283,
    ( *__receptor_type )[ "FBK_SPIKES_283" ] = 284,
    ( *__receptor_type )[ "FBK_SPIKES_284" ] = 285,
    ( *__receptor_type )[ "FBK_SPIKES_285" ] = 286,
    ( *__receptor_type )[ "FBK_SPIKES_286" ] = 287,
    ( *__receptor_type )[ "FBK_SPIKES_287" ] = 288,
    ( *__receptor_type )[ "FBK_SPIKES_288" ] = 289,
    ( *__receptor_type )[ "FBK_SPIKES_289" ] = 290,
    ( *__receptor_type )[ "FBK_SPIKES_290" ] = 291,
    ( *__receptor_type )[ "FBK_SPIKES_291" ] = 292,
    ( *__receptor_type )[ "FBK_SPIKES_292" ] = 293,
    ( *__receptor_type )[ "FBK_SPIKES_293" ] = 294,
    ( *__receptor_type )[ "FBK_SPIKES_294" ] = 295,
    ( *__receptor_type )[ "FBK_SPIKES_295" ] = 296,
    ( *__receptor_type )[ "FBK_SPIKES_296" ] = 297,
    ( *__receptor_type )[ "FBK_SPIKES_297" ] = 298,
    ( *__receptor_type )[ "FBK_SPIKES_298" ] = 299,
    ( *__receptor_type )[ "FBK_SPIKES_299" ] = 300,
    ( *__receptor_type )[ "FBK_SPIKES_300" ] = 301,
    ( *__receptor_type )[ "FBK_SPIKES_301" ] = 302,
    ( *__receptor_type )[ "FBK_SPIKES_302" ] = 303,
    ( *__receptor_type )[ "FBK_SPIKES_303" ] = 304,
    ( *__receptor_type )[ "FBK_SPIKES_304" ] = 305,
    ( *__receptor_type )[ "FBK_SPIKES_305" ] = 306,
    ( *__receptor_type )[ "FBK_SPIKES_306" ] = 307,
    ( *__receptor_type )[ "FBK_SPIKES_307" ] = 308,
    ( *__receptor_type )[ "FBK_SPIKES_308" ] = 309,
    ( *__receptor_type )[ "FBK_SPIKES_309" ] = 310,
    ( *__receptor_type )[ "FBK_SPIKES_310" ] = 311,
    ( *__receptor_type )[ "FBK_SPIKES_311" ] = 312,
    ( *__receptor_type )[ "FBK_SPIKES_312" ] = 313,
    ( *__receptor_type )[ "FBK_SPIKES_313" ] = 314,
    ( *__receptor_type )[ "FBK_SPIKES_314" ] = 315,
    ( *__receptor_type )[ "FBK_SPIKES_315" ] = 316,
    ( *__receptor_type )[ "FBK_SPIKES_316" ] = 317,
    ( *__receptor_type )[ "FBK_SPIKES_317" ] = 318,
    ( *__receptor_type )[ "FBK_SPIKES_318" ] = 319,
    ( *__receptor_type )[ "FBK_SPIKES_319" ] = 320,
    ( *__receptor_type )[ "FBK_SPIKES_320" ] = 321,
    ( *__receptor_type )[ "FBK_SPIKES_321" ] = 322,
    ( *__receptor_type )[ "FBK_SPIKES_322" ] = 323,
    ( *__receptor_type )[ "FBK_SPIKES_323" ] = 324,
    ( *__receptor_type )[ "FBK_SPIKES_324" ] = 325,
    ( *__receptor_type )[ "FBK_SPIKES_325" ] = 326,
    ( *__receptor_type )[ "FBK_SPIKES_326" ] = 327,
    ( *__receptor_type )[ "FBK_SPIKES_327" ] = 328,
    ( *__receptor_type )[ "FBK_SPIKES_328" ] = 329,
    ( *__receptor_type )[ "FBK_SPIKES_329" ] = 330,
    ( *__receptor_type )[ "FBK_SPIKES_330" ] = 331,
    ( *__receptor_type )[ "FBK_SPIKES_331" ] = 332,
    ( *__receptor_type )[ "FBK_SPIKES_332" ] = 333,
    ( *__receptor_type )[ "FBK_SPIKES_333" ] = 334,
    ( *__receptor_type )[ "FBK_SPIKES_334" ] = 335,
    ( *__receptor_type )[ "FBK_SPIKES_335" ] = 336,
    ( *__receptor_type )[ "FBK_SPIKES_336" ] = 337,
    ( *__receptor_type )[ "FBK_SPIKES_337" ] = 338,
    ( *__receptor_type )[ "FBK_SPIKES_338" ] = 339,
    ( *__receptor_type )[ "FBK_SPIKES_339" ] = 340,
    ( *__receptor_type )[ "FBK_SPIKES_340" ] = 341,
    ( *__receptor_type )[ "FBK_SPIKES_341" ] = 342,
    ( *__receptor_type )[ "FBK_SPIKES_342" ] = 343,
    ( *__receptor_type )[ "FBK_SPIKES_343" ] = 344,
    ( *__receptor_type )[ "FBK_SPIKES_344" ] = 345,
    ( *__receptor_type )[ "FBK_SPIKES_345" ] = 346,
    ( *__receptor_type )[ "FBK_SPIKES_346" ] = 347,
    ( *__receptor_type )[ "FBK_SPIKES_347" ] = 348,
    ( *__receptor_type )[ "FBK_SPIKES_348" ] = 349,
    ( *__receptor_type )[ "FBK_SPIKES_349" ] = 350,
    ( *__receptor_type )[ "FBK_SPIKES_350" ] = 351,
    ( *__receptor_type )[ "FBK_SPIKES_351" ] = 352,
    ( *__receptor_type )[ "FBK_SPIKES_352" ] = 353,
    ( *__receptor_type )[ "FBK_SPIKES_353" ] = 354,
    ( *__receptor_type )[ "FBK_SPIKES_354" ] = 355,
    ( *__receptor_type )[ "FBK_SPIKES_355" ] = 356,
    ( *__receptor_type )[ "FBK_SPIKES_356" ] = 357,
    ( *__receptor_type )[ "FBK_SPIKES_357" ] = 358,
    ( *__receptor_type )[ "FBK_SPIKES_358" ] = 359,
    ( *__receptor_type )[ "FBK_SPIKES_359" ] = 360,
    ( *__receptor_type )[ "FBK_SPIKES_360" ] = 361,
    ( *__receptor_type )[ "FBK_SPIKES_361" ] = 362,
    ( *__receptor_type )[ "FBK_SPIKES_362" ] = 363,
    ( *__receptor_type )[ "FBK_SPIKES_363" ] = 364,
    ( *__receptor_type )[ "FBK_SPIKES_364" ] = 365,
    ( *__receptor_type )[ "FBK_SPIKES_365" ] = 366,
    ( *__receptor_type )[ "FBK_SPIKES_366" ] = 367,
    ( *__receptor_type )[ "FBK_SPIKES_367" ] = 368,
    ( *__receptor_type )[ "FBK_SPIKES_368" ] = 369,
    ( *__receptor_type )[ "FBK_SPIKES_369" ] = 370,
    ( *__receptor_type )[ "FBK_SPIKES_370" ] = 371,
    ( *__receptor_type )[ "FBK_SPIKES_371" ] = 372,
    ( *__receptor_type )[ "FBK_SPIKES_372" ] = 373,
    ( *__receptor_type )[ "FBK_SPIKES_373" ] = 374,
    ( *__receptor_type )[ "FBK_SPIKES_374" ] = 375,
    ( *__receptor_type )[ "FBK_SPIKES_375" ] = 376,
    ( *__receptor_type )[ "FBK_SPIKES_376" ] = 377,
    ( *__receptor_type )[ "FBK_SPIKES_377" ] = 378,
    ( *__receptor_type )[ "FBK_SPIKES_378" ] = 379,
    ( *__receptor_type )[ "FBK_SPIKES_379" ] = 380,
    ( *__receptor_type )[ "FBK_SPIKES_380" ] = 381,
    ( *__receptor_type )[ "FBK_SPIKES_381" ] = 382,
    ( *__receptor_type )[ "FBK_SPIKES_382" ] = 383,
    ( *__receptor_type )[ "FBK_SPIKES_383" ] = 384,
    ( *__receptor_type )[ "FBK_SPIKES_384" ] = 385,
    ( *__receptor_type )[ "FBK_SPIKES_385" ] = 386,
    ( *__receptor_type )[ "FBK_SPIKES_386" ] = 387,
    ( *__receptor_type )[ "FBK_SPIKES_387" ] = 388,
    ( *__receptor_type )[ "FBK_SPIKES_388" ] = 389,
    ( *__receptor_type )[ "FBK_SPIKES_389" ] = 390,
    ( *__receptor_type )[ "FBK_SPIKES_390" ] = 391,
    ( *__receptor_type )[ "FBK_SPIKES_391" ] = 392,
    ( *__receptor_type )[ "FBK_SPIKES_392" ] = 393,
    ( *__receptor_type )[ "FBK_SPIKES_393" ] = 394,
    ( *__receptor_type )[ "FBK_SPIKES_394" ] = 395,
    ( *__receptor_type )[ "FBK_SPIKES_395" ] = 396,
    ( *__receptor_type )[ "FBK_SPIKES_396" ] = 397,
    ( *__receptor_type )[ "FBK_SPIKES_397" ] = 398,
    ( *__receptor_type )[ "FBK_SPIKES_398" ] = 399,
    ( *__receptor_type )[ "FBK_SPIKES_399" ] = 400,
    ( *__receptor_type )[ "PRED_SPIKES_0" ] = 401,
    ( *__receptor_type )[ "PRED_SPIKES_1" ] = 402,
    ( *__receptor_type )[ "PRED_SPIKES_2" ] = 403,
    ( *__receptor_type )[ "PRED_SPIKES_3" ] = 404,
    ( *__receptor_type )[ "PRED_SPIKES_4" ] = 405,
    ( *__receptor_type )[ "PRED_SPIKES_5" ] = 406,
    ( *__receptor_type )[ "PRED_SPIKES_6" ] = 407,
    ( *__receptor_type )[ "PRED_SPIKES_7" ] = 408,
    ( *__receptor_type )[ "PRED_SPIKES_8" ] = 409,
    ( *__receptor_type )[ "PRED_SPIKES_9" ] = 410,
    ( *__receptor_type )[ "PRED_SPIKES_10" ] = 411,
    ( *__receptor_type )[ "PRED_SPIKES_11" ] = 412,
    ( *__receptor_type )[ "PRED_SPIKES_12" ] = 413,
    ( *__receptor_type )[ "PRED_SPIKES_13" ] = 414,
    ( *__receptor_type )[ "PRED_SPIKES_14" ] = 415,
    ( *__receptor_type )[ "PRED_SPIKES_15" ] = 416,
    ( *__receptor_type )[ "PRED_SPIKES_16" ] = 417,
    ( *__receptor_type )[ "PRED_SPIKES_17" ] = 418,
    ( *__receptor_type )[ "PRED_SPIKES_18" ] = 419,
    ( *__receptor_type )[ "PRED_SPIKES_19" ] = 420,
    ( *__receptor_type )[ "PRED_SPIKES_20" ] = 421,
    ( *__receptor_type )[ "PRED_SPIKES_21" ] = 422,
    ( *__receptor_type )[ "PRED_SPIKES_22" ] = 423,
    ( *__receptor_type )[ "PRED_SPIKES_23" ] = 424,
    ( *__receptor_type )[ "PRED_SPIKES_24" ] = 425,
    ( *__receptor_type )[ "PRED_SPIKES_25" ] = 426,
    ( *__receptor_type )[ "PRED_SPIKES_26" ] = 427,
    ( *__receptor_type )[ "PRED_SPIKES_27" ] = 428,
    ( *__receptor_type )[ "PRED_SPIKES_28" ] = 429,
    ( *__receptor_type )[ "PRED_SPIKES_29" ] = 430,
    ( *__receptor_type )[ "PRED_SPIKES_30" ] = 431,
    ( *__receptor_type )[ "PRED_SPIKES_31" ] = 432,
    ( *__receptor_type )[ "PRED_SPIKES_32" ] = 433,
    ( *__receptor_type )[ "PRED_SPIKES_33" ] = 434,
    ( *__receptor_type )[ "PRED_SPIKES_34" ] = 435,
    ( *__receptor_type )[ "PRED_SPIKES_35" ] = 436,
    ( *__receptor_type )[ "PRED_SPIKES_36" ] = 437,
    ( *__receptor_type )[ "PRED_SPIKES_37" ] = 438,
    ( *__receptor_type )[ "PRED_SPIKES_38" ] = 439,
    ( *__receptor_type )[ "PRED_SPIKES_39" ] = 440,
    ( *__receptor_type )[ "PRED_SPIKES_40" ] = 441,
    ( *__receptor_type )[ "PRED_SPIKES_41" ] = 442,
    ( *__receptor_type )[ "PRED_SPIKES_42" ] = 443,
    ( *__receptor_type )[ "PRED_SPIKES_43" ] = 444,
    ( *__receptor_type )[ "PRED_SPIKES_44" ] = 445,
    ( *__receptor_type )[ "PRED_SPIKES_45" ] = 446,
    ( *__receptor_type )[ "PRED_SPIKES_46" ] = 447,
    ( *__receptor_type )[ "PRED_SPIKES_47" ] = 448,
    ( *__receptor_type )[ "PRED_SPIKES_48" ] = 449,
    ( *__receptor_type )[ "PRED_SPIKES_49" ] = 450,
    ( *__receptor_type )[ "PRED_SPIKES_50" ] = 451,
    ( *__receptor_type )[ "PRED_SPIKES_51" ] = 452,
    ( *__receptor_type )[ "PRED_SPIKES_52" ] = 453,
    ( *__receptor_type )[ "PRED_SPIKES_53" ] = 454,
    ( *__receptor_type )[ "PRED_SPIKES_54" ] = 455,
    ( *__receptor_type )[ "PRED_SPIKES_55" ] = 456,
    ( *__receptor_type )[ "PRED_SPIKES_56" ] = 457,
    ( *__receptor_type )[ "PRED_SPIKES_57" ] = 458,
    ( *__receptor_type )[ "PRED_SPIKES_58" ] = 459,
    ( *__receptor_type )[ "PRED_SPIKES_59" ] = 460,
    ( *__receptor_type )[ "PRED_SPIKES_60" ] = 461,
    ( *__receptor_type )[ "PRED_SPIKES_61" ] = 462,
    ( *__receptor_type )[ "PRED_SPIKES_62" ] = 463,
    ( *__receptor_type )[ "PRED_SPIKES_63" ] = 464,
    ( *__receptor_type )[ "PRED_SPIKES_64" ] = 465,
    ( *__receptor_type )[ "PRED_SPIKES_65" ] = 466,
    ( *__receptor_type )[ "PRED_SPIKES_66" ] = 467,
    ( *__receptor_type )[ "PRED_SPIKES_67" ] = 468,
    ( *__receptor_type )[ "PRED_SPIKES_68" ] = 469,
    ( *__receptor_type )[ "PRED_SPIKES_69" ] = 470,
    ( *__receptor_type )[ "PRED_SPIKES_70" ] = 471,
    ( *__receptor_type )[ "PRED_SPIKES_71" ] = 472,
    ( *__receptor_type )[ "PRED_SPIKES_72" ] = 473,
    ( *__receptor_type )[ "PRED_SPIKES_73" ] = 474,
    ( *__receptor_type )[ "PRED_SPIKES_74" ] = 475,
    ( *__receptor_type )[ "PRED_SPIKES_75" ] = 476,
    ( *__receptor_type )[ "PRED_SPIKES_76" ] = 477,
    ( *__receptor_type )[ "PRED_SPIKES_77" ] = 478,
    ( *__receptor_type )[ "PRED_SPIKES_78" ] = 479,
    ( *__receptor_type )[ "PRED_SPIKES_79" ] = 480,
    ( *__receptor_type )[ "PRED_SPIKES_80" ] = 481,
    ( *__receptor_type )[ "PRED_SPIKES_81" ] = 482,
    ( *__receptor_type )[ "PRED_SPIKES_82" ] = 483,
    ( *__receptor_type )[ "PRED_SPIKES_83" ] = 484,
    ( *__receptor_type )[ "PRED_SPIKES_84" ] = 485,
    ( *__receptor_type )[ "PRED_SPIKES_85" ] = 486,
    ( *__receptor_type )[ "PRED_SPIKES_86" ] = 487,
    ( *__receptor_type )[ "PRED_SPIKES_87" ] = 488,
    ( *__receptor_type )[ "PRED_SPIKES_88" ] = 489,
    ( *__receptor_type )[ "PRED_SPIKES_89" ] = 490,
    ( *__receptor_type )[ "PRED_SPIKES_90" ] = 491,
    ( *__receptor_type )[ "PRED_SPIKES_91" ] = 492,
    ( *__receptor_type )[ "PRED_SPIKES_92" ] = 493,
    ( *__receptor_type )[ "PRED_SPIKES_93" ] = 494,
    ( *__receptor_type )[ "PRED_SPIKES_94" ] = 495,
    ( *__receptor_type )[ "PRED_SPIKES_95" ] = 496,
    ( *__receptor_type )[ "PRED_SPIKES_96" ] = 497,
    ( *__receptor_type )[ "PRED_SPIKES_97" ] = 498,
    ( *__receptor_type )[ "PRED_SPIKES_98" ] = 499,
    ( *__receptor_type )[ "PRED_SPIKES_99" ] = 500,
    ( *__receptor_type )[ "PRED_SPIKES_100" ] = 501,
    ( *__receptor_type )[ "PRED_SPIKES_101" ] = 502,
    ( *__receptor_type )[ "PRED_SPIKES_102" ] = 503,
    ( *__receptor_type )[ "PRED_SPIKES_103" ] = 504,
    ( *__receptor_type )[ "PRED_SPIKES_104" ] = 505,
    ( *__receptor_type )[ "PRED_SPIKES_105" ] = 506,
    ( *__receptor_type )[ "PRED_SPIKES_106" ] = 507,
    ( *__receptor_type )[ "PRED_SPIKES_107" ] = 508,
    ( *__receptor_type )[ "PRED_SPIKES_108" ] = 509,
    ( *__receptor_type )[ "PRED_SPIKES_109" ] = 510,
    ( *__receptor_type )[ "PRED_SPIKES_110" ] = 511,
    ( *__receptor_type )[ "PRED_SPIKES_111" ] = 512,
    ( *__receptor_type )[ "PRED_SPIKES_112" ] = 513,
    ( *__receptor_type )[ "PRED_SPIKES_113" ] = 514,
    ( *__receptor_type )[ "PRED_SPIKES_114" ] = 515,
    ( *__receptor_type )[ "PRED_SPIKES_115" ] = 516,
    ( *__receptor_type )[ "PRED_SPIKES_116" ] = 517,
    ( *__receptor_type )[ "PRED_SPIKES_117" ] = 518,
    ( *__receptor_type )[ "PRED_SPIKES_118" ] = 519,
    ( *__receptor_type )[ "PRED_SPIKES_119" ] = 520,
    ( *__receptor_type )[ "PRED_SPIKES_120" ] = 521,
    ( *__receptor_type )[ "PRED_SPIKES_121" ] = 522,
    ( *__receptor_type )[ "PRED_SPIKES_122" ] = 523,
    ( *__receptor_type )[ "PRED_SPIKES_123" ] = 524,
    ( *__receptor_type )[ "PRED_SPIKES_124" ] = 525,
    ( *__receptor_type )[ "PRED_SPIKES_125" ] = 526,
    ( *__receptor_type )[ "PRED_SPIKES_126" ] = 527,
    ( *__receptor_type )[ "PRED_SPIKES_127" ] = 528,
    ( *__receptor_type )[ "PRED_SPIKES_128" ] = 529,
    ( *__receptor_type )[ "PRED_SPIKES_129" ] = 530,
    ( *__receptor_type )[ "PRED_SPIKES_130" ] = 531,
    ( *__receptor_type )[ "PRED_SPIKES_131" ] = 532,
    ( *__receptor_type )[ "PRED_SPIKES_132" ] = 533,
    ( *__receptor_type )[ "PRED_SPIKES_133" ] = 534,
    ( *__receptor_type )[ "PRED_SPIKES_134" ] = 535,
    ( *__receptor_type )[ "PRED_SPIKES_135" ] = 536,
    ( *__receptor_type )[ "PRED_SPIKES_136" ] = 537,
    ( *__receptor_type )[ "PRED_SPIKES_137" ] = 538,
    ( *__receptor_type )[ "PRED_SPIKES_138" ] = 539,
    ( *__receptor_type )[ "PRED_SPIKES_139" ] = 540,
    ( *__receptor_type )[ "PRED_SPIKES_140" ] = 541,
    ( *__receptor_type )[ "PRED_SPIKES_141" ] = 542,
    ( *__receptor_type )[ "PRED_SPIKES_142" ] = 543,
    ( *__receptor_type )[ "PRED_SPIKES_143" ] = 544,
    ( *__receptor_type )[ "PRED_SPIKES_144" ] = 545,
    ( *__receptor_type )[ "PRED_SPIKES_145" ] = 546,
    ( *__receptor_type )[ "PRED_SPIKES_146" ] = 547,
    ( *__receptor_type )[ "PRED_SPIKES_147" ] = 548,
    ( *__receptor_type )[ "PRED_SPIKES_148" ] = 549,
    ( *__receptor_type )[ "PRED_SPIKES_149" ] = 550,
    ( *__receptor_type )[ "PRED_SPIKES_150" ] = 551,
    ( *__receptor_type )[ "PRED_SPIKES_151" ] = 552,
    ( *__receptor_type )[ "PRED_SPIKES_152" ] = 553,
    ( *__receptor_type )[ "PRED_SPIKES_153" ] = 554,
    ( *__receptor_type )[ "PRED_SPIKES_154" ] = 555,
    ( *__receptor_type )[ "PRED_SPIKES_155" ] = 556,
    ( *__receptor_type )[ "PRED_SPIKES_156" ] = 557,
    ( *__receptor_type )[ "PRED_SPIKES_157" ] = 558,
    ( *__receptor_type )[ "PRED_SPIKES_158" ] = 559,
    ( *__receptor_type )[ "PRED_SPIKES_159" ] = 560,
    ( *__receptor_type )[ "PRED_SPIKES_160" ] = 561,
    ( *__receptor_type )[ "PRED_SPIKES_161" ] = 562,
    ( *__receptor_type )[ "PRED_SPIKES_162" ] = 563,
    ( *__receptor_type )[ "PRED_SPIKES_163" ] = 564,
    ( *__receptor_type )[ "PRED_SPIKES_164" ] = 565,
    ( *__receptor_type )[ "PRED_SPIKES_165" ] = 566,
    ( *__receptor_type )[ "PRED_SPIKES_166" ] = 567,
    ( *__receptor_type )[ "PRED_SPIKES_167" ] = 568,
    ( *__receptor_type )[ "PRED_SPIKES_168" ] = 569,
    ( *__receptor_type )[ "PRED_SPIKES_169" ] = 570,
    ( *__receptor_type )[ "PRED_SPIKES_170" ] = 571,
    ( *__receptor_type )[ "PRED_SPIKES_171" ] = 572,
    ( *__receptor_type )[ "PRED_SPIKES_172" ] = 573,
    ( *__receptor_type )[ "PRED_SPIKES_173" ] = 574,
    ( *__receptor_type )[ "PRED_SPIKES_174" ] = 575,
    ( *__receptor_type )[ "PRED_SPIKES_175" ] = 576,
    ( *__receptor_type )[ "PRED_SPIKES_176" ] = 577,
    ( *__receptor_type )[ "PRED_SPIKES_177" ] = 578,
    ( *__receptor_type )[ "PRED_SPIKES_178" ] = 579,
    ( *__receptor_type )[ "PRED_SPIKES_179" ] = 580,
    ( *__receptor_type )[ "PRED_SPIKES_180" ] = 581,
    ( *__receptor_type )[ "PRED_SPIKES_181" ] = 582,
    ( *__receptor_type )[ "PRED_SPIKES_182" ] = 583,
    ( *__receptor_type )[ "PRED_SPIKES_183" ] = 584,
    ( *__receptor_type )[ "PRED_SPIKES_184" ] = 585,
    ( *__receptor_type )[ "PRED_SPIKES_185" ] = 586,
    ( *__receptor_type )[ "PRED_SPIKES_186" ] = 587,
    ( *__receptor_type )[ "PRED_SPIKES_187" ] = 588,
    ( *__receptor_type )[ "PRED_SPIKES_188" ] = 589,
    ( *__receptor_type )[ "PRED_SPIKES_189" ] = 590,
    ( *__receptor_type )[ "PRED_SPIKES_190" ] = 591,
    ( *__receptor_type )[ "PRED_SPIKES_191" ] = 592,
    ( *__receptor_type )[ "PRED_SPIKES_192" ] = 593,
    ( *__receptor_type )[ "PRED_SPIKES_193" ] = 594,
    ( *__receptor_type )[ "PRED_SPIKES_194" ] = 595,
    ( *__receptor_type )[ "PRED_SPIKES_195" ] = 596,
    ( *__receptor_type )[ "PRED_SPIKES_196" ] = 597,
    ( *__receptor_type )[ "PRED_SPIKES_197" ] = 598,
    ( *__receptor_type )[ "PRED_SPIKES_198" ] = 599,
    ( *__receptor_type )[ "PRED_SPIKES_199" ] = 600,
    ( *__receptor_type )[ "PRED_SPIKES_200" ] = 601,
    ( *__receptor_type )[ "PRED_SPIKES_201" ] = 602,
    ( *__receptor_type )[ "PRED_SPIKES_202" ] = 603,
    ( *__receptor_type )[ "PRED_SPIKES_203" ] = 604,
    ( *__receptor_type )[ "PRED_SPIKES_204" ] = 605,
    ( *__receptor_type )[ "PRED_SPIKES_205" ] = 606,
    ( *__receptor_type )[ "PRED_SPIKES_206" ] = 607,
    ( *__receptor_type )[ "PRED_SPIKES_207" ] = 608,
    ( *__receptor_type )[ "PRED_SPIKES_208" ] = 609,
    ( *__receptor_type )[ "PRED_SPIKES_209" ] = 610,
    ( *__receptor_type )[ "PRED_SPIKES_210" ] = 611,
    ( *__receptor_type )[ "PRED_SPIKES_211" ] = 612,
    ( *__receptor_type )[ "PRED_SPIKES_212" ] = 613,
    ( *__receptor_type )[ "PRED_SPIKES_213" ] = 614,
    ( *__receptor_type )[ "PRED_SPIKES_214" ] = 615,
    ( *__receptor_type )[ "PRED_SPIKES_215" ] = 616,
    ( *__receptor_type )[ "PRED_SPIKES_216" ] = 617,
    ( *__receptor_type )[ "PRED_SPIKES_217" ] = 618,
    ( *__receptor_type )[ "PRED_SPIKES_218" ] = 619,
    ( *__receptor_type )[ "PRED_SPIKES_219" ] = 620,
    ( *__receptor_type )[ "PRED_SPIKES_220" ] = 621,
    ( *__receptor_type )[ "PRED_SPIKES_221" ] = 622,
    ( *__receptor_type )[ "PRED_SPIKES_222" ] = 623,
    ( *__receptor_type )[ "PRED_SPIKES_223" ] = 624,
    ( *__receptor_type )[ "PRED_SPIKES_224" ] = 625,
    ( *__receptor_type )[ "PRED_SPIKES_225" ] = 626,
    ( *__receptor_type )[ "PRED_SPIKES_226" ] = 627,
    ( *__receptor_type )[ "PRED_SPIKES_227" ] = 628,
    ( *__receptor_type )[ "PRED_SPIKES_228" ] = 629,
    ( *__receptor_type )[ "PRED_SPIKES_229" ] = 630,
    ( *__receptor_type )[ "PRED_SPIKES_230" ] = 631,
    ( *__receptor_type )[ "PRED_SPIKES_231" ] = 632,
    ( *__receptor_type )[ "PRED_SPIKES_232" ] = 633,
    ( *__receptor_type )[ "PRED_SPIKES_233" ] = 634,
    ( *__receptor_type )[ "PRED_SPIKES_234" ] = 635,
    ( *__receptor_type )[ "PRED_SPIKES_235" ] = 636,
    ( *__receptor_type )[ "PRED_SPIKES_236" ] = 637,
    ( *__receptor_type )[ "PRED_SPIKES_237" ] = 638,
    ( *__receptor_type )[ "PRED_SPIKES_238" ] = 639,
    ( *__receptor_type )[ "PRED_SPIKES_239" ] = 640,
    ( *__receptor_type )[ "PRED_SPIKES_240" ] = 641,
    ( *__receptor_type )[ "PRED_SPIKES_241" ] = 642,
    ( *__receptor_type )[ "PRED_SPIKES_242" ] = 643,
    ( *__receptor_type )[ "PRED_SPIKES_243" ] = 644,
    ( *__receptor_type )[ "PRED_SPIKES_244" ] = 645,
    ( *__receptor_type )[ "PRED_SPIKES_245" ] = 646,
    ( *__receptor_type )[ "PRED_SPIKES_246" ] = 647,
    ( *__receptor_type )[ "PRED_SPIKES_247" ] = 648,
    ( *__receptor_type )[ "PRED_SPIKES_248" ] = 649,
    ( *__receptor_type )[ "PRED_SPIKES_249" ] = 650,
    ( *__receptor_type )[ "PRED_SPIKES_250" ] = 651,
    ( *__receptor_type )[ "PRED_SPIKES_251" ] = 652,
    ( *__receptor_type )[ "PRED_SPIKES_252" ] = 653,
    ( *__receptor_type )[ "PRED_SPIKES_253" ] = 654,
    ( *__receptor_type )[ "PRED_SPIKES_254" ] = 655,
    ( *__receptor_type )[ "PRED_SPIKES_255" ] = 656,
    ( *__receptor_type )[ "PRED_SPIKES_256" ] = 657,
    ( *__receptor_type )[ "PRED_SPIKES_257" ] = 658,
    ( *__receptor_type )[ "PRED_SPIKES_258" ] = 659,
    ( *__receptor_type )[ "PRED_SPIKES_259" ] = 660,
    ( *__receptor_type )[ "PRED_SPIKES_260" ] = 661,
    ( *__receptor_type )[ "PRED_SPIKES_261" ] = 662,
    ( *__receptor_type )[ "PRED_SPIKES_262" ] = 663,
    ( *__receptor_type )[ "PRED_SPIKES_263" ] = 664,
    ( *__receptor_type )[ "PRED_SPIKES_264" ] = 665,
    ( *__receptor_type )[ "PRED_SPIKES_265" ] = 666,
    ( *__receptor_type )[ "PRED_SPIKES_266" ] = 667,
    ( *__receptor_type )[ "PRED_SPIKES_267" ] = 668,
    ( *__receptor_type )[ "PRED_SPIKES_268" ] = 669,
    ( *__receptor_type )[ "PRED_SPIKES_269" ] = 670,
    ( *__receptor_type )[ "PRED_SPIKES_270" ] = 671,
    ( *__receptor_type )[ "PRED_SPIKES_271" ] = 672,
    ( *__receptor_type )[ "PRED_SPIKES_272" ] = 673,
    ( *__receptor_type )[ "PRED_SPIKES_273" ] = 674,
    ( *__receptor_type )[ "PRED_SPIKES_274" ] = 675,
    ( *__receptor_type )[ "PRED_SPIKES_275" ] = 676,
    ( *__receptor_type )[ "PRED_SPIKES_276" ] = 677,
    ( *__receptor_type )[ "PRED_SPIKES_277" ] = 678,
    ( *__receptor_type )[ "PRED_SPIKES_278" ] = 679,
    ( *__receptor_type )[ "PRED_SPIKES_279" ] = 680,
    ( *__receptor_type )[ "PRED_SPIKES_280" ] = 681,
    ( *__receptor_type )[ "PRED_SPIKES_281" ] = 682,
    ( *__receptor_type )[ "PRED_SPIKES_282" ] = 683,
    ( *__receptor_type )[ "PRED_SPIKES_283" ] = 684,
    ( *__receptor_type )[ "PRED_SPIKES_284" ] = 685,
    ( *__receptor_type )[ "PRED_SPIKES_285" ] = 686,
    ( *__receptor_type )[ "PRED_SPIKES_286" ] = 687,
    ( *__receptor_type )[ "PRED_SPIKES_287" ] = 688,
    ( *__receptor_type )[ "PRED_SPIKES_288" ] = 689,
    ( *__receptor_type )[ "PRED_SPIKES_289" ] = 690,
    ( *__receptor_type )[ "PRED_SPIKES_290" ] = 691,
    ( *__receptor_type )[ "PRED_SPIKES_291" ] = 692,
    ( *__receptor_type )[ "PRED_SPIKES_292" ] = 693,
    ( *__receptor_type )[ "PRED_SPIKES_293" ] = 694,
    ( *__receptor_type )[ "PRED_SPIKES_294" ] = 695,
    ( *__receptor_type )[ "PRED_SPIKES_295" ] = 696,
    ( *__receptor_type )[ "PRED_SPIKES_296" ] = 697,
    ( *__receptor_type )[ "PRED_SPIKES_297" ] = 698,
    ( *__receptor_type )[ "PRED_SPIKES_298" ] = 699,
    ( *__receptor_type )[ "PRED_SPIKES_299" ] = 700,
    ( *__receptor_type )[ "PRED_SPIKES_300" ] = 701,
    ( *__receptor_type )[ "PRED_SPIKES_301" ] = 702,
    ( *__receptor_type )[ "PRED_SPIKES_302" ] = 703,
    ( *__receptor_type )[ "PRED_SPIKES_303" ] = 704,
    ( *__receptor_type )[ "PRED_SPIKES_304" ] = 705,
    ( *__receptor_type )[ "PRED_SPIKES_305" ] = 706,
    ( *__receptor_type )[ "PRED_SPIKES_306" ] = 707,
    ( *__receptor_type )[ "PRED_SPIKES_307" ] = 708,
    ( *__receptor_type )[ "PRED_SPIKES_308" ] = 709,
    ( *__receptor_type )[ "PRED_SPIKES_309" ] = 710,
    ( *__receptor_type )[ "PRED_SPIKES_310" ] = 711,
    ( *__receptor_type )[ "PRED_SPIKES_311" ] = 712,
    ( *__receptor_type )[ "PRED_SPIKES_312" ] = 713,
    ( *__receptor_type )[ "PRED_SPIKES_313" ] = 714,
    ( *__receptor_type )[ "PRED_SPIKES_314" ] = 715,
    ( *__receptor_type )[ "PRED_SPIKES_315" ] = 716,
    ( *__receptor_type )[ "PRED_SPIKES_316" ] = 717,
    ( *__receptor_type )[ "PRED_SPIKES_317" ] = 718,
    ( *__receptor_type )[ "PRED_SPIKES_318" ] = 719,
    ( *__receptor_type )[ "PRED_SPIKES_319" ] = 720,
    ( *__receptor_type )[ "PRED_SPIKES_320" ] = 721,
    ( *__receptor_type )[ "PRED_SPIKES_321" ] = 722,
    ( *__receptor_type )[ "PRED_SPIKES_322" ] = 723,
    ( *__receptor_type )[ "PRED_SPIKES_323" ] = 724,
    ( *__receptor_type )[ "PRED_SPIKES_324" ] = 725,
    ( *__receptor_type )[ "PRED_SPIKES_325" ] = 726,
    ( *__receptor_type )[ "PRED_SPIKES_326" ] = 727,
    ( *__receptor_type )[ "PRED_SPIKES_327" ] = 728,
    ( *__receptor_type )[ "PRED_SPIKES_328" ] = 729,
    ( *__receptor_type )[ "PRED_SPIKES_329" ] = 730,
    ( *__receptor_type )[ "PRED_SPIKES_330" ] = 731,
    ( *__receptor_type )[ "PRED_SPIKES_331" ] = 732,
    ( *__receptor_type )[ "PRED_SPIKES_332" ] = 733,
    ( *__receptor_type )[ "PRED_SPIKES_333" ] = 734,
    ( *__receptor_type )[ "PRED_SPIKES_334" ] = 735,
    ( *__receptor_type )[ "PRED_SPIKES_335" ] = 736,
    ( *__receptor_type )[ "PRED_SPIKES_336" ] = 737,
    ( *__receptor_type )[ "PRED_SPIKES_337" ] = 738,
    ( *__receptor_type )[ "PRED_SPIKES_338" ] = 739,
    ( *__receptor_type )[ "PRED_SPIKES_339" ] = 740,
    ( *__receptor_type )[ "PRED_SPIKES_340" ] = 741,
    ( *__receptor_type )[ "PRED_SPIKES_341" ] = 742,
    ( *__receptor_type )[ "PRED_SPIKES_342" ] = 743,
    ( *__receptor_type )[ "PRED_SPIKES_343" ] = 744,
    ( *__receptor_type )[ "PRED_SPIKES_344" ] = 745,
    ( *__receptor_type )[ "PRED_SPIKES_345" ] = 746,
    ( *__receptor_type )[ "PRED_SPIKES_346" ] = 747,
    ( *__receptor_type )[ "PRED_SPIKES_347" ] = 748,
    ( *__receptor_type )[ "PRED_SPIKES_348" ] = 749,
    ( *__receptor_type )[ "PRED_SPIKES_349" ] = 750,
    ( *__receptor_type )[ "PRED_SPIKES_350" ] = 751,
    ( *__receptor_type )[ "PRED_SPIKES_351" ] = 752,
    ( *__receptor_type )[ "PRED_SPIKES_352" ] = 753,
    ( *__receptor_type )[ "PRED_SPIKES_353" ] = 754,
    ( *__receptor_type )[ "PRED_SPIKES_354" ] = 755,
    ( *__receptor_type )[ "PRED_SPIKES_355" ] = 756,
    ( *__receptor_type )[ "PRED_SPIKES_356" ] = 757,
    ( *__receptor_type )[ "PRED_SPIKES_357" ] = 758,
    ( *__receptor_type )[ "PRED_SPIKES_358" ] = 759,
    ( *__receptor_type )[ "PRED_SPIKES_359" ] = 760,
    ( *__receptor_type )[ "PRED_SPIKES_360" ] = 761,
    ( *__receptor_type )[ "PRED_SPIKES_361" ] = 762,
    ( *__receptor_type )[ "PRED_SPIKES_362" ] = 763,
    ( *__receptor_type )[ "PRED_SPIKES_363" ] = 764,
    ( *__receptor_type )[ "PRED_SPIKES_364" ] = 765,
    ( *__receptor_type )[ "PRED_SPIKES_365" ] = 766,
    ( *__receptor_type )[ "PRED_SPIKES_366" ] = 767,
    ( *__receptor_type )[ "PRED_SPIKES_367" ] = 768,
    ( *__receptor_type )[ "PRED_SPIKES_368" ] = 769,
    ( *__receptor_type )[ "PRED_SPIKES_369" ] = 770,
    ( *__receptor_type )[ "PRED_SPIKES_370" ] = 771,
    ( *__receptor_type )[ "PRED_SPIKES_371" ] = 772,
    ( *__receptor_type )[ "PRED_SPIKES_372" ] = 773,
    ( *__receptor_type )[ "PRED_SPIKES_373" ] = 774,
    ( *__receptor_type )[ "PRED_SPIKES_374" ] = 775,
    ( *__receptor_type )[ "PRED_SPIKES_375" ] = 776,
    ( *__receptor_type )[ "PRED_SPIKES_376" ] = 777,
    ( *__receptor_type )[ "PRED_SPIKES_377" ] = 778,
    ( *__receptor_type )[ "PRED_SPIKES_378" ] = 779,
    ( *__receptor_type )[ "PRED_SPIKES_379" ] = 780,
    ( *__receptor_type )[ "PRED_SPIKES_380" ] = 781,
    ( *__receptor_type )[ "PRED_SPIKES_381" ] = 782,
    ( *__receptor_type )[ "PRED_SPIKES_382" ] = 783,
    ( *__receptor_type )[ "PRED_SPIKES_383" ] = 784,
    ( *__receptor_type )[ "PRED_SPIKES_384" ] = 785,
    ( *__receptor_type )[ "PRED_SPIKES_385" ] = 786,
    ( *__receptor_type )[ "PRED_SPIKES_386" ] = 787,
    ( *__receptor_type )[ "PRED_SPIKES_387" ] = 788,
    ( *__receptor_type )[ "PRED_SPIKES_388" ] = 789,
    ( *__receptor_type )[ "PRED_SPIKES_389" ] = 790,
    ( *__receptor_type )[ "PRED_SPIKES_390" ] = 791,
    ( *__receptor_type )[ "PRED_SPIKES_391" ] = 792,
    ( *__receptor_type )[ "PRED_SPIKES_392" ] = 793,
    ( *__receptor_type )[ "PRED_SPIKES_393" ] = 794,
    ( *__receptor_type )[ "PRED_SPIKES_394" ] = 795,
    ( *__receptor_type )[ "PRED_SPIKES_395" ] = 796,
    ( *__receptor_type )[ "PRED_SPIKES_396" ] = 797,
    ( *__receptor_type )[ "PRED_SPIKES_397" ] = 798,
    ( *__receptor_type )[ "PRED_SPIKES_398" ] = 799,
    ( *__receptor_type )[ "PRED_SPIKES_399" ] = 800,
    ( *__d )[ "receptor_types" ] = __receptor_type;

  (*__d)[nest::names::recordables] = recordablesMap_.get_list();
}

inline void state_neuron::set_status(const DictionaryDatum &__d)
{
  // parameters
  double tmp_kp = get_kp();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_kp, tmp_kp, this);
  // Resize vectors
  if (tmp_kp != get_kp())
  {
  }
  bool tmp_pos = get_pos();
  nest::updateValueParam<bool>(__d, nest::state_neuron_names::_pos, tmp_pos, this);
  // Resize vectors
  if (tmp_pos != get_pos())
  {
  }
  double tmp_base_rate = get_base_rate();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_base_rate, tmp_base_rate, this);
  // Resize vectors
  if (tmp_base_rate != get_base_rate())
  {
  }
  double tmp_buffer_size = get_buffer_size();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_buffer_size, tmp_buffer_size, this);
  // Resize vectors
  if (tmp_buffer_size != get_buffer_size())
  {
  }
  long tmp_simulation_steps = get_simulation_steps();
  nest::updateValueParam<long>(__d, nest::state_neuron_names::_simulation_steps, tmp_simulation_steps, this);
  // Resize vectors
  if (tmp_simulation_steps != get_simulation_steps())
  {
  }
  long tmp_N_fbk = get_N_fbk();
  nest::updateValueParam<long>(__d, nest::state_neuron_names::_N_fbk, tmp_N_fbk, this);
  // Resize vectors
  if (tmp_N_fbk != get_N_fbk())
  {
    std::vector< double >  _tmp_current_fbk_input = get_current_fbk_input();
    _tmp_current_fbk_input.resize(tmp_N_fbk, 0.);
    set_current_fbk_input(_tmp_current_fbk_input);
    std::vector< double >  _tmp_fbk_counts = get_fbk_counts();
    _tmp_fbk_counts.resize(tmp_N_fbk, 0.);
    set_fbk_counts(_tmp_fbk_counts);
  }
  long tmp_N_pred = get_N_pred();
  nest::updateValueParam<long>(__d, nest::state_neuron_names::_N_pred, tmp_N_pred, this);
  // Resize vectors
  if (tmp_N_pred != get_N_pred())
  {
    std::vector< double >  _tmp_current_pred_input = get_current_pred_input();
    _tmp_current_pred_input.resize(tmp_N_pred, 0.);
    set_current_pred_input(_tmp_current_pred_input);
    std::vector< double >  _tmp_pred_counts = get_pred_counts();
    _tmp_pred_counts.resize(tmp_N_pred, 0.);
    set_pred_counts(_tmp_pred_counts);
  }
  long tmp_fbk_bf_size = get_fbk_bf_size();
  nest::updateValueParam<long>(__d, nest::state_neuron_names::_fbk_bf_size, tmp_fbk_bf_size, this);
  // Resize vectors
  if (tmp_fbk_bf_size != get_fbk_bf_size())
  {
    std::vector< double >  _tmp_fbk_buffer = get_fbk_buffer();
    _tmp_fbk_buffer.resize(tmp_fbk_bf_size, 0.);
    set_fbk_buffer(_tmp_fbk_buffer);
  }
  long tmp_pred_bf_size = get_pred_bf_size();
  nest::updateValueParam<long>(__d, nest::state_neuron_names::_pred_bf_size, tmp_pred_bf_size, this);
  // Resize vectors
  if (tmp_pred_bf_size != get_pred_bf_size())
  {
    std::vector< double >  _tmp_pred_buffer = get_pred_buffer();
    _tmp_pred_buffer.resize(tmp_pred_bf_size, 0.);
    set_pred_buffer(_tmp_pred_buffer);
  }
  double tmp_time_wait = get_time_wait();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_time_wait, tmp_time_wait, this);
  // Resize vectors
  if (tmp_time_wait != get_time_wait())
  {
  }
  double tmp_time_trial = get_time_trial();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_time_trial, tmp_time_trial, this);
  // Resize vectors
  if (tmp_time_trial != get_time_trial())
  {
  }

  // initial values for state variables in ODE or kernel
  double tmp_in_rate = get_in_rate();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_in_rate, tmp_in_rate, this);
  double tmp_out_rate = get_out_rate();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_out_rate, tmp_out_rate, this);
  long tmp_spike_count_out = get_spike_count_out();
  nest::updateValueParam<long>(__d, nest::state_neuron_names::_spike_count_out, tmp_spike_count_out, this);
  std::vector< double >  tmp_current_fbk_input = get_current_fbk_input();
  updateValue<std::vector< double > >(__d, nest::state_neuron_names::_current_fbk_input, tmp_current_fbk_input);
   
  // Check if the new vector size matches its original size
  if ( tmp_current_fbk_input.size() != tmp_N_fbk )
  {
    std::stringstream msg;
    msg << "The vector \"current_fbk_input\" does not match its size: " << tmp_N_fbk;
    throw nest::BadProperty(msg.str());
  }
  std::vector< double >  tmp_current_pred_input = get_current_pred_input();
  updateValue<std::vector< double > >(__d, nest::state_neuron_names::_current_pred_input, tmp_current_pred_input);
   
  // Check if the new vector size matches its original size
  if ( tmp_current_pred_input.size() != tmp_N_pred )
  {
    std::stringstream msg;
    msg << "The vector \"current_pred_input\" does not match its size: " << tmp_N_pred;
    throw nest::BadProperty(msg.str());
  }
  std::vector< double >  tmp_fbk_buffer = get_fbk_buffer();
  updateValue<std::vector< double > >(__d, nest::state_neuron_names::_fbk_buffer, tmp_fbk_buffer);
   
  // Check if the new vector size matches its original size
  if ( tmp_fbk_buffer.size() != tmp_fbk_bf_size )
  {
    std::stringstream msg;
    msg << "The vector \"fbk_buffer\" does not match its size: " << tmp_fbk_bf_size;
    throw nest::BadProperty(msg.str());
  }
  std::vector< double >  tmp_pred_buffer = get_pred_buffer();
  updateValue<std::vector< double > >(__d, nest::state_neuron_names::_pred_buffer, tmp_pred_buffer);
   
  // Check if the new vector size matches its original size
  if ( tmp_pred_buffer.size() != tmp_pred_bf_size )
  {
    std::stringstream msg;
    msg << "The vector \"pred_buffer\" does not match its size: " << tmp_pred_bf_size;
    throw nest::BadProperty(msg.str());
  }
  std::vector< double >  tmp_fbk_counts = get_fbk_counts();
  updateValue<std::vector< double > >(__d, nest::state_neuron_names::_fbk_counts, tmp_fbk_counts);
   
  // Check if the new vector size matches its original size
  if ( tmp_fbk_counts.size() != tmp_N_fbk )
  {
    std::stringstream msg;
    msg << "The vector \"fbk_counts\" does not match its size: " << tmp_N_fbk;
    throw nest::BadProperty(msg.str());
  }
  std::vector< double >  tmp_pred_counts = get_pred_counts();
  updateValue<std::vector< double > >(__d, nest::state_neuron_names::_pred_counts, tmp_pred_counts);
   
  // Check if the new vector size matches its original size
  if ( tmp_pred_counts.size() != tmp_N_pred )
  {
    std::stringstream msg;
    msg << "The vector \"pred_counts\" does not match its size: " << tmp_N_pred;
    throw nest::BadProperty(msg.str());
  }
  long tmp_tick = get_tick();
  nest::updateValueParam<long>(__d, nest::state_neuron_names::_tick, tmp_tick, this);
  long tmp_position_count = get_position_count();
  nest::updateValueParam<long>(__d, nest::state_neuron_names::_position_count, tmp_position_count, this);
  double tmp_mean_fbk = get_mean_fbk();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_mean_fbk, tmp_mean_fbk, this);
  double tmp_mean_pred = get_mean_pred();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_mean_pred, tmp_mean_pred, this);
  double tmp_var_fbk = get_var_fbk();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_var_fbk, tmp_var_fbk, this);
  double tmp_var_pred = get_var_pred();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_var_pred, tmp_var_pred, this);
  double tmp_CV_fbk = get_CV_fbk();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_CV_fbk, tmp_CV_fbk, this);
  double tmp_CV_pred = get_CV_pred();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_CV_pred, tmp_CV_pred, this);
  double tmp_total_CV = get_total_CV();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_total_CV, tmp_total_CV, this);
  double tmp_lambda_poisson = get_lambda_poisson();
  nest::updateValueParam<double>(__d, nest::state_neuron_names::_lambda_poisson, tmp_lambda_poisson, this);

  // We now know that (ptmp, stmp) are consistent. We do not
  // write them back to (P_, S_) before we are also sure that
  // the properties to be set in the parent class are internally
  // consistent.
  ArchivingNode::set_status(__d);

  // if we get here, temporaries contain consistent set of properties
  set_kp(tmp_kp);
  set_pos(tmp_pos);
  set_base_rate(tmp_base_rate);
  set_buffer_size(tmp_buffer_size);
  set_simulation_steps(tmp_simulation_steps);
  set_N_fbk(tmp_N_fbk);
  set_N_pred(tmp_N_pred);
  set_fbk_bf_size(tmp_fbk_bf_size);
  set_pred_bf_size(tmp_pred_bf_size);
  set_time_wait(tmp_time_wait);
  set_time_trial(tmp_time_trial);
  set_in_rate(tmp_in_rate);
  set_out_rate(tmp_out_rate);
  set_spike_count_out(tmp_spike_count_out);
  set_current_fbk_input(tmp_current_fbk_input);
  set_current_pred_input(tmp_current_pred_input);
  set_fbk_buffer(tmp_fbk_buffer);
  set_pred_buffer(tmp_pred_buffer);
  set_fbk_counts(tmp_fbk_counts);
  set_pred_counts(tmp_pred_counts);
  set_tick(tmp_tick);
  set_position_count(tmp_position_count);
  set_mean_fbk(tmp_mean_fbk);
  set_mean_pred(tmp_mean_pred);
  set_var_fbk(tmp_var_fbk);
  set_var_pred(tmp_var_pred);
  set_CV_fbk(tmp_CV_fbk);
  set_CV_pred(tmp_CV_pred);
  set_total_CV(tmp_total_CV);
  set_lambda_poisson(tmp_lambda_poisson);





  // recompute internal variables in case they are dependent on parameters or state that might have been updated in this call to set_status()
  recompute_internal_variables();
};



#endif /* #ifndef STATE_NEURON */
