from rlcore.algo import PPO
from rlcore.storage import RolloutStorage


class Neo(object):

  def __init__(self, args, policy, obs_shape, action_space):
    super().__init__()

    self.obs_shape = obs_shape
    self.action_space = action_space
    self.actor_critic = policy        # it is MPNN instance
    self.rollouts = RolloutStorage(args.num_steps, args.num_processes, self.obs_shape, self.action_space, 
                                   recurrent_hidden_state_size=1)
    self.args = args
    self.trainer = PPO(self.actor_critic, args.clip_param, args.ppo_epoch, args.num_mini_batch, args.value_loss_coef,
                       args.entropy_coef, lr=args.lr,max_grad_norm=args.max_grad_norm)
    self.alive = True ##
    
  def load_model(self, policy_state):
      self.actor_critic.load_state_dict(policy_state)

  def initialize_obs(self, obs):
    # this function is called at the start of episode
    self.rollouts.reset()
    self.rollouts.obs[0].copy_(obs)

  def initialize_new_episode(self, step, obs, masks):
    ## one rollout can have multiple episodes
    self.rollouts.obs[step].copy_(obs)
    self.rollouts.masks[step].copy_(masks)

  def update_rollout(self, obs, reward, mask, done, record_just_died, chosen_attacker):
    self.rollouts.insert(obs, self.states, self.action, self.action_log_prob, self.value, reward, mask, done, record_just_died, chosen_attacker)

  def act(self, step, deterministic=False):
    self.value, self.action, self.action_log_prob, self.states = self.actor_critic.act(self.rollouts.obs[step],
              self.rollouts.recurrent_hidden_states[step],self.rollouts.masks[step],deterministic=deterministic)
    return self.action

  def wrap_horizon(self, next_value, start_pt, end_pt):
    self.rollouts.compute_returns(next_value, True, self.args.gamma, self.args.tau, start_pt, end_pt)

  def before_update(self):
    self.rollouts.before_update()

  def after_update(self):
    self.rollouts.after_update()

  def update(self):
    return self.trainer.update(self.rollouts)