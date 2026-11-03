#!/usr/bin/env node
import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { App } from 'aws-cdk-lib';
import { readAgentCoreProject, resolveTargetStacks, transformAgentCoreJson } from '@aws/agentcore-cdk';
import { AgentCoreStack, type RuntimeEnv } from '../lib/cdk-stack';

try {
  // The AgentCore CLI runs this app from agentcore/cdk/; readAgentCoreProject walks up to agentcore/.
  const project = readAgentCoreProject();
  // Per target: the env vars and the config parameter of every runtime, written by `mise run ac-gen`.
  const runtimeEnvPath = join(project.configRoot, 'runtime-env.json');
  const runtimeEnvs: Record<string, RuntimeEnv> = existsSync(runtimeEnvPath)
    ? JSON.parse(readFileSync(runtimeEnvPath, 'utf-8'))
    : {};
  const app = new App();
  for (const stack of resolveTargetStacks({
    projectName: project.projectName,
    targets: project.targets,
    deployedState: project.deployedState,
  })) {
    let runtimeEnv: RuntimeEnv | undefined;
    if (stack.target) {
      runtimeEnv = runtimeEnvs[stack.target.name];
      if (!runtimeEnv) {
        throw new Error(`no target '${stack.target.name}' in ${runtimeEnvPath}, run \`mise run ac-gen\``);
      }
    }
    new AgentCoreStack(app, stack.stackName, {
      runtimeEnv,
      env: stack.env,
      tags: stack.tags,
      description: stack.description,
      application: transformAgentCoreJson(project.agentCoreJson, {
        projectRoot: project.projectRoot,
        credentials: stack.credentials,
        target: stack.target,
      }),
    });
  }
  app.synth();
} catch (error) {
  console.error('AgentCore CDK synthesis failed:', error instanceof Error ? error.message : error);
  process.exit(1);
}
